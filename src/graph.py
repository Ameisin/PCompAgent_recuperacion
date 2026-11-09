"""Grafo multiagente de PCompAgent: supervisor ↔ especialistas + HITL.

Flujo:
  START → supervisor ──┬── requisitos ───┐
                       ├── componentes ──┼──► supervisor → …
                       └── sintetizar ───┘
                                 │
                  FINISH ──┬── aplicar (interrupt_before → decisión humana) → END
                           └── END  (faltan datos: se pregunta al usuario; no hay plan que aprobar)

Roles:
  - supervisor:  elige el siguiente rol (LLM) con reglas de respaldo en Python.
  - requisitos:  traduce el pedido a requisitos técnicos (puede usar tools).
  - componentes: elige piezas concretas del catálogo y comprueba compatibilidad (tools).
  - sintetizar:  une las notas en respuesta + plan (viñetas) y deja el flujo listo para HITL.
  - aplicar:     solo tras la decisión humana; cierra (done) o resetea para otro intento.

Stack: LangChain (ChatGoogleGenerativeAI + @tool) + LangGraph (MemorySaver).
"""

import re
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src import config_grafo
from src.guardrails import (
    calcular_faltan_datos,
    extraer_preferencias,
    pregunta_aclaratoria,
    resumen_presupuesto,
)
from src.llm import get_llm
from src.registro_tools import TOOLS, describir_tools, ejecutar_tool


def _acumular(actual: list, nuevo: list) -> list:
    """Reducer de LangGraph: concatena listas (no pisa el valor anterior)."""
    return (actual or []) + (nuevo or [])


class EstadoGrafo(TypedDict):
    pedido: str  # mensaje del usuario en este turno
    historial: Annotated[list, _acumular]  # mensajes y decisiones HITL del hilo (persisten entre turnos)
    preferencias: dict  # presupuesto / usos / categorías (las extrae Python, no el LLM)
    faltan_datos: list  # datos mínimos que faltan para recomendar (Python)
    notas_requisitos: str  # las escribe el especialista requisitos
    notas_componentes: str  # las escribe el especialista componentes
    respuesta: str  # texto para el usuario (sintetizar / aplicar / pregunta aclaratoria)
    plan: list  # viñetas del plan (≥2 para HITL)
    resumen_presupuesto: dict  # suma de precios del plan vs presupuesto (Python)
    siguiente: str  # lo elige el supervisor: requisitos|componentes|sintetizar|FINISH
    iteracion: int  # contador del supervisor (tope MAX_ITER)
    log: Annotated[list, _acumular]  # traza legible del orquestador
    traza_tools: Annotated[list, _acumular]  # tools usadas en los especialistas
    max_steps: int  # tope modelo↔tools dentro de un especialista
    plan_aprobado: bool  # lo escribe el humano vía update_state (HITL)
    comentario_humano: str  # motivo opcional del rechazo (lo escribe el humano)
    done: bool  # True solo tras aprobar en aplicar
    pendiente_hitl: bool  # True mientras el grafo está pausado antes de aplicar


OPCIONES = ("requisitos", "componentes", "sintetizar", "FINISH")


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------


def _preview(texto: str, n: int = 120) -> str:
    t = (texto or "").replace("\n", " ").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def _texto_llm(content: Any) -> str:
    """Normaliza ai.content (str o lista de bloques Gemini) a texto plano."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        partes: list[str] = []
        for bloque in content:
            if isinstance(bloque, str):
                partes.append(bloque)
            elif isinstance(bloque, dict):
                t = bloque.get("text") or bloque.get("content") or ""
                if t:
                    partes.append(str(t))
            else:
                t = getattr(bloque, "text", None)
                if t:
                    partes.append(str(t))
        return "\n".join(p.strip() for p in partes if p and str(p).strip()).strip()
    return str(content).strip()


def _parse_plan(texto: str) -> list[str]:
    """Extrae viñetas (- / • / *) del texto del plan.

    La marca debe ir seguida de un espacio: así un título en negrita Markdown
    ("**Configuración gaming**") no se confunde con una viñeta.
    """
    items: list[str] = []
    for line in (texto or "").splitlines():
        m = re.match(r"^\s*[-•*]\s+(.+)$", line)
        if m:
            items.append(m.group(1).strip())
    return [i for i in items if i]


def _historial_prompt(estado: EstadoGrafo) -> str:
    """Últimas entradas del hilo, para que los especialistas vean el contexto.

    Sin esto, tras un rechazo ("más barato, por favor") el siguiente turno
    empezaría de cero aunque el checkpointer recuerde la conversación.
    """
    entradas = (estado.get("historial") or [])[-config_grafo.MAX_HISTORIAL_PROMPT :]
    if not entradas:
        return "(sin historial)"
    return "\n".join(f"- [{e.get('rol')}] {e.get('texto')}" for e in entradas)


def _textos_preferencias(estado: EstadoGrafo) -> list[str]:
    """Lo que dijo la persona en el hilo, en orden: sus mensajes y los motivos de rechazo.

    El motivo del HITL ("como mucho 550 USD") también es una preferencia y
    debe pesar en el siguiente plan (y en la suma del presupuesto).
    """
    textos = []
    for e in estado.get("historial") or []:
        if e.get("rol") == "usuario":
            textos.append(e.get("texto", ""))
        elif e.get("rol") == "humano_hitl" and e.get("motivo"):
            textos.append(e["motivo"])
    return textos


# ---------------------------------------------------------------------------
# Mini-bucle de tools dentro de un especialista (Sprint 12 → Sprint 13)
# ---------------------------------------------------------------------------


def _ejecutar_con_tools(
    system: str,
    user: str,
    max_steps: int,
) -> tuple[str, list[dict[str, Any]]]:
    """Mini-bucle agent↔tools dentro de un especialista.

    El LLM puede pedir tools; Python las ejecuta (allowlist).
    Se repite hasta que haya texto final o se agote max_steps.
    """
    llm = get_llm().bind_tools(TOOLS)
    messages: list = [SystemMessage(content=system), HumanMessage(content=user)]
    traza: list[dict[str, Any]] = []
    resultados: list[str] = []  # lo que devolvieron las tools (para notas parciales)
    texto = ""

    for paso in range(1, max(1, max_steps) + 1):
        ai: AIMessage = llm.invoke(messages)
        messages.append(ai)
        calls = getattr(ai, "tool_calls", None) or []
        if not calls:
            # Sin tool_calls → el modelo ya respondió en texto
            texto = _texto_llm(ai.content)
            break
        for call in calls:
            nombre = call.get("name") or ""
            args = dict(call.get("args") or {})
            resultado = ejecutar_tool(nombre, args)
            status = "blocked" if "no está permitida" in resultado else (
                "error" if resultado.startswith("Error") else "ok"
            )
            traza.append(
                {
                    "step": paso,
                    "tool": nombre,
                    "args": args,
                    "status": status,
                    "preview": _preview(resultado),
                }
            )
            if status == "ok":
                resultados.append(f"[{nombre}] {_preview(resultado, 600)}")
            messages.append(
                ToolMessage(content=resultado, tool_call_id=call.get("id") or nombre)
            )
    else:
        # Se agotó max_steps con el modelo aún pidiendo tools: en vez de un
        # mensaje vacío, se conserva lo que sí devolvieron las tools.
        texto = texto or (
            "He parado por max_steps en el especialista. Datos obtenidos de las tools:\n"
            + ("\n".join(resultados) if resultados else "(ninguno)")
        )

    return texto, traza


# ---------------------------------------------------------------------------
# Supervisor
# ---------------------------------------------------------------------------


def _fallback_siguiente(estado: EstadoGrafo) -> str:
    """Si el LLM falla o responde mal: reglas deterministas en Python."""
    if estado.get("faltan_datos"):
        return "FINISH"  # hay que preguntar al usuario antes de seguir
    if not (estado.get("notas_requisitos") or "").strip():
        return "requisitos"
    if not (estado.get("notas_componentes") or "").strip():
        return "componentes"
    if not (estado.get("respuesta") or "").strip():
        return "sintetizar"
    return "FINISH"


def _eleccion_valida(siguiente: str, estado: EstadoGrafo) -> bool:
    """Precondiciones de cada rol: el LLM propone, Python comprueba que tenga sentido.

    Evita saltarse pasos (sintetizar sin componentes, cerrar sin plan) y
    repetir un rol cuyo trabajo ya está hecho en este turno (cada repetición
    es una llamada más a la API sin información nueva).
    """
    tiene = {
        "requisitos": bool((estado.get("notas_requisitos") or "").strip()),
        "componentes": bool((estado.get("notas_componentes") or "").strip()),
        "plan": bool(estado.get("plan")),
        "respuesta": bool((estado.get("respuesta") or "").strip()),
    }
    if siguiente == "requisitos":
        return not tiene["requisitos"]
    if siguiente == "componentes":
        return tiene["requisitos"] and not tiene["componentes"]
    if siguiente == "sintetizar":
        return tiene["componentes"] and not tiene["plan"]
    if siguiente == "FINISH":
        return tiene["respuesta"] or tiene["plan"]
    return False  # cualquier otra palabra no es un nodo


def nodo_supervisor(estado: EstadoGrafo) -> dict:
    """Orquesta: no escribe el plan; solo elige el siguiente nodo (o FINISH).

    MAX_ITER evita bucles infinitos supervisor ↔ especialistas.
    """
    it = int(estado.get("iteracion") or 0) + 1
    if it >= config_grafo.MAX_ITER:
        return {
            "iteracion": it,
            "siguiente": "FINISH",
            "log": [f"iter {it}: supervisor → FINISH (MAX_ITER)"],
        }
    if estado.get("faltan_datos"):
        # Regla dura en Python: sin datos mínimos no se recomienda nada.
        return {
            "iteracion": it,
            "siguiente": "FINISH",
            "log": [f"iter {it}: supervisor → FINISH (faltan datos: {', '.join(estado['faltan_datos'])})"],
        }

    if not config_grafo.SUPERVISOR_USA_LLM:
        siguiente, origen = _fallback_siguiente(estado), "reglas"
    else:
        llm = get_llm(temperature=config_grafo.TEMPERATURE_SUPERVISOR)
        prompt = (
            "Eres el supervisor de un asesor de compra de PC.\n"
            "Elige el siguiente rol:\n"
            "- requisitos: traduce el pedido a requisitos técnicos (uso, rendimiento, reparto del presupuesto)\n"
            "- componentes: elige piezas concretas del catálogo y comprueba su compatibilidad\n"
            "- sintetizar: une las notas en un plan final con viñetas\n"
            "- FINISH: ya hay plan/respuesta lista\n"
            "Responde SOLO una palabra: requisitos, componentes, sintetizar o FINISH.\n"
            "Regla: sin notas_requisitos → requisitos; sin notas_componentes → componentes; "
            "con ambas y sin respuesta → sintetizar; con respuesta → FINISH.\n\n"
            f"pedido: {estado.get('pedido')}\n"
            f"notas_requisitos: {(estado.get('notas_requisitos') or '')[:400]}\n"
            f"notas_componentes: {(estado.get('notas_componentes') or '')[:400]}\n"
            f"respuesta: {(estado.get('respuesta') or '')[:200]}\n"
        )
        try:
            out = llm.invoke([HumanMessage(content=prompt)])
            raw = _texto_llm(out.content)
            palabra = re.findall(r"[A-Za-z_]+", raw)
            siguiente, origen = (palabra[0] if palabra else "").strip(), "llm"
            if not _eleccion_valida(siguiente, estado):
                siguiente, origen = _fallback_siguiente(estado), f"fallback (LLM dijo {raw[:30]!r})"
        except Exception as e:  # noqa: BLE001
            siguiente, origen = _fallback_siguiente(estado), f"fallback (error LLM: {type(e).__name__})"

    return {
        "iteracion": it,
        "siguiente": siguiente,
        "log": [f"iter {it}: supervisor → {siguiente} [{origen}]"],
    }


# ---------------------------------------------------------------------------
# Especialistas
# ---------------------------------------------------------------------------


def nodo_requisitos(estado: EstadoGrafo) -> dict:
    """Especialista: escribe notas_requisitos (puede usar tools). No elige piezas.

    Antes de gastar llamadas al LLM, Python comprueba si faltan datos mínimos
    (presupuesto / uso). Si faltan, deja una pregunta para el usuario y el
    supervisor cierra el turno sin plan (no hay nada que aprobar en HITL).
    """
    preferencias = extraer_preferencias(_textos_preferencias(estado) or [estado.get("pedido") or ""])
    faltan = calcular_faltan_datos(preferencias)
    if faltan:
        return {
            "preferencias": preferencias,
            "faltan_datos": faltan,
            "notas_requisitos": f"Faltan datos para recomendar: {', '.join(faltan)}.",
            "respuesta": pregunta_aclaratoria(faltan),
            "log": [f"requisitos: faltan datos ({', '.join(faltan)}) → se pregunta al usuario"],
        }

    max_steps = int(estado.get("max_steps") or config_grafo.MAX_STEPS_DEFAULT)
    system = (
        "Eres el especialista REQUISITOS de un asesor de compra de PC. "
        "Tu oficio es traducir el pedido del usuario a requisitos técnicos mínimos. "
        "NO eliges modelos concretos ni redactas el plan final.\n\n"
        f"Tools disponibles:\n{describir_tools()}\n\n"
        "Reglas:\n"
        "- Consulta el RAG solo cuando aporte: requisitos de un videojuego concreto o "
        "recomendaciones de las guías de compra (p. ej. potencia de la fuente). Para el "
        "reparto genérico del presupuesto no hace falta.\n"
        "- Si el usuario habla de una imagen, foto, captura o ficha, léela con la tool de "
        "imagen. Si da el presupuesto en una moneda distinta de USD, conviértelo con la tool "
        "de divisas (los precios del catálogo están en USD).\n"
        "- No inventes datos que debería darte una tool; si la tool no tiene la información, dilo.\n"
        "- Devuelve notas breves en español: uso, objetivo de rendimiento, requisitos por "
        "componente (CPU, GPU, RAM, almacenamiento, fuente) y un reparto orientativo del "
        "presupuesto en USD. Si se pide una sola pieza, céntrate en esa pieza."
    )
    user = (
        f"Pedido del usuario:\n{estado.get('pedido')}\n\n"
        f"Historial de la conversación:\n{_historial_prompt(estado)}\n\n"
        f"Preferencias detectadas (Python): {preferencias}\n\n"
        "Devuelve solo las notas de requisitos."
    )
    texto, traza = _ejecutar_con_tools(system, user, max_steps)
    return {
        "preferencias": preferencias,
        "faltan_datos": [],
        "notas_requisitos": texto,
        "traza_tools": traza,
        "log": [f"requisitos: notas listas ({len(traza)} tools)"],
    }


def nodo_componentes(estado: EstadoGrafo) -> dict:
    """Especialista: escribe notas_componentes (piezas concretas + compatibilidad; tools)."""
    max_steps = int(estado.get("max_steps") or config_grafo.MAX_STEPS_DEFAULT)
    system = (
        "Eres el especialista COMPONENTES de un asesor de compra de PC. "
        "Tu oficio es elegir piezas CONCRETAS del catálogo que cumplan los requisitos y el "
        "presupuesto, y comprobar su compatibilidad: socket CPU↔placa base, tipo de memoria "
        "(DDR4/DDR5), formato de placa↔caja y potencia de la fuente. No redactas el plan final.\n\n"
        f"Tools disponibles:\n{describir_tools()}\n\n"
        "Reglas:\n"
        "- Busca las piezas con buscar_componentes, UNA llamada por categoría con el rango de "
        "precio del reparto (p. ej. componente='gpu', precio_min=220, precio_max=300). Puedes "
        "pedir varias búsquedas en la misma respuesta. Usa el RAG solo para dudas de "
        "compatibilidad o requisitos de juegos.\n"
        "- Encadena la compatibilidad: primero procesador y gráfica; después la placa base "
        "con el socket del procesador elegido y la RAM con el tipo de memoria de esa placa.\n"
        "- Usa SOLO nombres y precios que devuelva la tool. Si una categoría no aparece, "
        "escribe 'sin dato en el catálogo'; no propongas modelos de memoria.\n"
        "- Una línea por pieza: 'Categoría: Modelo — precio USD (fuente)'.\n"
        "- Si con ese presupuesto no se puede cumplir el objetivo, dilo con honestidad y "
        "propón la alternativa más cercana.\n"
        "- Si se pide una sola pieza, recomienda solo esa pieza (1-3 opciones)."
    )
    user = (
        f"Pedido:\n{estado.get('pedido')}\n\n"
        f"Historial de la conversación:\n{_historial_prompt(estado)}\n\n"
        f"Preferencias detectadas (Python): {estado.get('preferencias')}\n\n"
        f"Notas de requisitos:\n{estado.get('notas_requisitos') or '(aún no)'}\n\n"
        "Devuelve solo las notas de componentes."
    )
    texto, traza = _ejecutar_con_tools(system, user, max_steps)
    return {
        "notas_componentes": texto,
        "traza_tools": traza,
        "log": [f"componentes: notas listas ({len(traza)} tools)"],
    }


def nodo_sintetizar(estado: EstadoGrafo) -> dict:
    """Une las notas en respuesta + plan (viñetas). Deja el flujo listo para HITL."""
    llm = get_llm()
    prompt = (
        "Une las notas en una propuesta de configuración de PC breve, en español.\n"
        "Formato:\n"
        "- Una intro de 1-2 frases.\n"
        "- Una viñeta por componente que empiece por '- ' con el formato "
        "'Categoría: Modelo — precio USD'.\n"
        "- Si se piden dos configuraciones (comparativa), un título para cada una con sus viñetas.\n"
        "- Al final, una línea 'Total estimado: X USD' y una frase sobre la compatibilidad.\n"
        "Usa SOLO los modelos y precios que aparecen en las notas; no inventes ninguno. "
        "Si a una categoría le falta el dato, ponla como 'pendiente (sin dato en el catálogo)' "
        "sin precio. Si el objetivo no es alcanzable con el presupuesto, dilo claramente.\n\n"
        f"Pedido: {estado.get('pedido')}\n"
        f"Historial: {_historial_prompt(estado)}\n"
        f"Requisitos: {estado.get('notas_requisitos')}\n"
        f"Componentes: {estado.get('notas_componentes')}\n"
    )
    out = llm.invoke([HumanMessage(content=prompt)])
    texto = _texto_llm(out.content)
    plan = _parse_plan(texto)
    if len(plan) < 2:
        # Fallback mínimo para poder pausar en HITL con algo que mostrar
        plan = [
            p
            for p in (
                (estado.get("notas_requisitos") or "").split(".")[0].strip(),
                (estado.get("notas_componentes") or "").split(".")[0].strip(),
            )
            if p
        ]
        if len(plan) < 2:
            plan = ["Configuración según requisitos del usuario", "Revisar compatibilidad y precios"]
        texto = texto or "Plan propuesto:\n" + "\n".join(f"- {p}" for p in plan)

    # Comprobación en Python ANTES de la pausa: la persona aprueba con el dato real.
    preferencias = estado.get("preferencias") or {}
    resumen = resumen_presupuesto(
        plan, preferencias.get("presupuesto"), n_usos=len(preferencias.get("usos") or [])
    )
    if resumen.get("dentro") is False:
        texto += (
            f"\n\nAviso: la suma de precios del plan ({resumen['total']:.2f} USD) supera el "
            f"presupuesto indicado ({resumen['presupuesto']:.2f})."
        )
    return {
        "respuesta": texto,
        "plan": plan,
        "resumen_presupuesto": resumen,
        "pendiente_hitl": True,
        "log": ["sintetizar: plan listo (pendiente HITL)"],
    }


def nodo_aplicar(estado: EstadoGrafo) -> dict:
    """Cierra o resetea según plan_aprobado.

    Solo se ejecuta DESPUÉS de la decisión humana: el grafo pausa con
    interrupt_before; el cliente hace update_state + invoke(None).
    """
    if estado.get("plan_aprobado"):
        prev = (estado.get("respuesta") or "").strip()
        cierre = "Plan aprobado. ¡Configuración lista!"
        return {
            "done": True,
            "pendiente_hitl": False,
            "respuesta": f"{prev}\n\n{cierre}".strip() if prev else cierre,
            "historial": [{"rol": "humano_hitl", "texto": "aprobó el plan"}],
            "log": ["aplicar: plan aprobado"],
        }

    comentario = (estado.get("comentario_humano") or "").strip()
    plan_rechazado = "; ".join(estado.get("plan") or [])
    return {
        "done": False,
        "pendiente_hitl": False,
        "plan_aprobado": False,
        "plan": [],
        "resumen_presupuesto": {},
        "respuesta": (
            "Plan rechazado. Dime qué cambiar (presupuesto, uso, alguna pieza…) "
            "y propongo otra configuración."
            + (f"\n\nHe tomado nota: '{comentario}'." if comentario else "")
        ),
        "notas_requisitos": "",
        "notas_componentes": "",
        # Queda en el hilo: el siguiente turno sabe qué no gustó y por qué.
        "historial": [
            {
                "rol": "humano_hitl",
                "texto": f"rechazó el plan ({_preview(plan_rechazado, 300)})"
                + (f". Motivo: {comentario}" if comentario else ""),
                "motivo": comentario,
            }
        ],
        "log": ["aplicar: plan rechazado" + (f" (motivo: {comentario})" if comentario else "")],
    }


# ---------------------------------------------------------------------------
# Router y construcción del grafo
# ---------------------------------------------------------------------------


def _router_supervisor(
    estado: EstadoGrafo,
) -> Literal["requisitos", "componentes", "sintetizar", "aplicar", "__end__"]:
    """Lee estado['siguiente'] y elige el edge.

    FINISH → nodo aplicar (donde está el interrupt HITL).
    FINISH con datos pendientes → END: se responde con la pregunta aclaratoria.
    Si aún no hay plan/respuesta → sintetizar antes de pausar.
    """
    sig = (estado.get("siguiente") or "").strip()
    if sig == "FINISH":
        if estado.get("faltan_datos"):
            return "__end__"
        if not (estado.get("plan") or estado.get("respuesta")):
            return "sintetizar"
        return "aplicar"
    if sig in ("requisitos", "componentes", "sintetizar"):
        return sig  # type: ignore[return-value]
    return "sintetizar"


def build_graph():
    """Monta el grafo: especialistas vuelven al supervisor; HITL ante aplicar."""
    grafo = StateGraph(EstadoGrafo)
    grafo.add_node("supervisor", nodo_supervisor)
    grafo.add_node("requisitos", nodo_requisitos)
    grafo.add_node("componentes", nodo_componentes)
    grafo.add_node("sintetizar", nodo_sintetizar)
    grafo.add_node("aplicar", nodo_aplicar)

    grafo.add_edge(START, "supervisor")
    grafo.add_conditional_edges(
        "supervisor",
        _router_supervisor,
        {
            "requisitos": "requisitos",
            "componentes": "componentes",
            "sintetizar": "sintetizar",
            "aplicar": "aplicar",
            "__end__": END,
        },
    )
    # Tras cada especialista, el control vuelve al supervisor
    grafo.add_edge("requisitos", "supervisor")
    grafo.add_edge("componentes", "supervisor")
    grafo.add_edge("sintetizar", "supervisor")
    grafo.add_edge("aplicar", END)

    return grafo.compile(
        checkpointer=MemorySaver(),  # checkpoints por thread_id
        interrupt_before=["aplicar"],  # pausa HITL antes de este nodo
    )


_APP = None


def get_app():
    """Grafo compilado único por proceso: el MemorySaver vive dentro.

    Si se compilara uno nuevo en cada turno, cada compilación traería un
    MemorySaver vacío y se perderían los hilos (y las pausas HITL).
    """
    global _APP
    if _APP is None:
        _APP = build_graph()
    return _APP


def config_hilo(thread_id: str) -> dict:
    """Config de LangGraph: identifica el hilo del checkpointer."""
    return {"configurable": {"thread_id": thread_id}}


def estado_inicial_grafo(pedido: str, max_steps: int | None = None) -> EstadoGrafo:
    """Entrada de un turno nuevo en el hilo.

    Los campos sin reducer se sustituyen (notas, plan, flags…) y el turno
    empieza limpio; los que tienen reducer (historial, log, traza_tools) se
    ACUMULAN sobre el checkpoint: así el hilo recuerda lo que se habló antes.
    """
    return {
        "pedido": pedido,
        "historial": [{"rol": "usuario", "texto": pedido}],
        "preferencias": {},
        "faltan_datos": [],
        "notas_requisitos": "",
        "notas_componentes": "",
        "respuesta": "",
        "plan": [],
        "resumen_presupuesto": {},
        "siguiente": "",
        "iteracion": 0,
        "log": [],
        "traza_tools": [],
        "max_steps": max_steps if max_steps is not None else config_grafo.MAX_STEPS_DEFAULT,
        "plan_aprobado": False,
        "comentario_humano": "",
        "done": False,
        "pendiente_hitl": False,
    }


def hay_interrupt(thread_id: str) -> bool:
    """True si el hilo está pausado antes de aplicar (HITL pendiente).

    get_state(...).next incluye el nombre del siguiente nodo bloqueado.
    """
    snap = get_app().get_state(config_hilo(thread_id))
    nxt = snap.next or ()
    return "aplicar" in nxt
