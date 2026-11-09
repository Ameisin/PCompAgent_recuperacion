"""Comprobaciones del grafo multiagente SIN llamar a Gemini ni a Chroma.

  python -m src.verificar_grafo

Mismo estilo que verificar.py de la Live Review (Sprint 13), ampliado: además
de las comprobaciones estructurales, ejecuta el grafo de punta a punta con un
LLM simulado (_LLMFalso) para probar el HITL (aprobar / rechazar), la memoria
por thread_id, las guardas y los topes sin gastar cuota de la API gratuita.
"""

import inspect
import sys

from langchain_core.messages import AIMessage, ToolMessage

from src import config_grafo
from src import graph as gmod


# ---------------------------------------------------------------------------
# LLM simulado
# ---------------------------------------------------------------------------


class _LLMFalso:
    """Imita la interfaz que usa el grafo de ChatGoogleGenerativeAI (bind_tools + invoke).

    Responde según el rol que reconoce en el prompt:
      - supervisor:  una palabra inválida → obliga a usar el fallback de Python.
      - requisitos:  primero pide una tool NO permitida (prueba la allowlist), luego texto.
      - componentes: texto con piezas y precios.
      - sintetizar:  plan con viñetas y precios.
    """

    def __init__(self) -> None:
        self.llamadas: list[str] = []

    def bind_tools(self, _tools):
        return self

    def invoke(self, messages):
        primero = str(messages[0].content)
        if "supervisor" in primero:
            self.llamadas.append("supervisor")
            return AIMessage(content="no_se_que_toca")
        if "REQUISITOS" in primero:
            self.llamadas.append("requisitos")
            if isinstance(messages[-1], ToolMessage):
                return AIMessage(content="Uso gaming 1080p. CPU de 6 núcleos, GPU de 8 GB, 16 GB DDR4.")
            return AIMessage(
                content="",
                tool_calls=[{"name": "tool_inventada", "args": {}, "id": "call_1"}],
            )
        if "COMPONENTES" in primero:
            self.llamadas.append("componentes")
            return AIMessage(
                content="CPU: AMD Ryzen 5 5600 — 129.99 USD (cpu.csv)\nGPU: RX 6600 — 199.99 USD (video-card.csv)"
            )
        self.llamadas.append("sintetizar")
        return AIMessage(
            content=(
                "Propuesta para jugar a 1080p:\n"
                "- CPU: AMD Ryzen 5 5600 — 129.99 USD\n"
                "- GPU: RX 6600 — 199.99 USD\n"
                "Total estimado: 329.98 USD"
            )
        )


def _con_llm_falso() -> _LLMFalso:
    """Sustituye get_llm del grafo por el LLM simulado (los nodos lo leen al ejecutarse)."""
    falso = _LLMFalso()
    gmod.get_llm = lambda temperature=None: falso  # type: ignore[assignment]
    config_grafo.SUPERVISOR_USA_LLM = True
    return falso


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def _fallback_ok() -> tuple[bool, str]:
    casos = [
        ({"faltan_datos": ["uso"]}, "FINISH"),
        ({"notas_requisitos": "", "notas_componentes": "", "respuesta": ""}, "requisitos"),
        ({"notas_requisitos": "req", "notas_componentes": "", "respuesta": ""}, "componentes"),
        ({"notas_requisitos": "req", "notas_componentes": "comp", "respuesta": ""}, "sintetizar"),
        ({"notas_requisitos": "req", "notas_componentes": "comp", "respuesta": "plan"}, "FINISH"),
    ]
    for estado, esperado in casos:
        got = gmod._fallback_siguiente(estado)  # type: ignore[arg-type]
        if got != esperado:
            return False, f"_fallback_siguiente({estado!r}) → {got!r}, esperaba {esperado!r}"
    return True, f"{len(casos)} casos OK"


def _eleccion_valida_ok() -> tuple[bool, str]:
    casos = [
        ("inventado", {}, False),
        ("requisitos", {}, True),
        ("requisitos", {"notas_requisitos": "ya hechas"}, False),  # no repetir un rol hecho
        ("componentes", {"notas_requisitos": ""}, False),
        ("sintetizar", {"notas_componentes": "x"}, True),
        ("sintetizar", {"notas_componentes": "x", "plan": ["a", "b"]}, False),  # ya hay plan
        ("FINISH", {"respuesta": "", "plan": []}, False),
    ]
    for sig, estado, esperado in casos:
        if gmod._eleccion_valida(sig, estado) != esperado:  # type: ignore[arg-type]
            return False, f"_eleccion_valida({sig!r}, {estado!r}) debería ser {esperado}"
    return True, f"{len(casos)} casos OK"


def _guardrails_ok() -> tuple[bool, str]:
    from src.guardrails import calcular_faltan_datos, extraer_preferencias, resumen_presupuesto

    p1 = extraer_preferencias(["Quiero una PC gamer para jugar a 1080p, presupuesto de $700."])
    if p1["presupuesto"] != 700 or "gaming" not in p1["usos"] or calcular_faltan_datos(p1):
        return False, f"pedido completo mal interpretado: {p1}"
    p2 = extraer_preferencias(["Quiero armar una PC pero no sé cuánto presupuesto tengo"])
    if calcular_faltan_datos(p2) != ["presupuesto", "uso"]:
        return False, f"pedido ambiguo debería pedir presupuesto y uso: {p2}"
    p3 = extraer_preferencias(["¿Qué SSD me recomiendas para edición de video 4K?"])
    if calcular_faltan_datos(p3):
        return False, "una pieza suelta no necesita presupuesto"
    r = resumen_presupuesto(["CPU — 129.99 USD", "GPU — 600 USD", "Total: 729.99 USD"], 700)
    if r["total"] != 729.99 or r["dentro"] is not False:
        return False, f"resumen_presupuesto incorrecto: {r}"
    return True, "preferencias, faltan_datos y presupuesto OK"


def _allowlist_ok() -> tuple[bool, str]:
    from src.registro_tools import TOOLS, ejecutar_tool

    if not TOOLS:
        return False, "TOOLS está vacía"
    bloqueada = ejecutar_tool("borrar_disco", {})
    if "no está permitida" not in bloqueada:
        return False, f"la allowlist no bloquea tools desconocidas: {bloqueada!r}"
    return True, f"bloquea nombres no registrados ({len(TOOLS)} tools permitidas)"


def _tools_aisladas_ok() -> tuple[bool, str]:
    """Las 4 categorías del PB2 funcionan fuera del grafo (sin gastar API)."""
    from src import config_grafo
    from src.tools import divisas, ejecutar_tool

    rag = ejecutar_tool("RAG_consultar_catalogo", {"consulta": "  "})
    if "vacía" not in rag:
        return False, f"RAG: una consulta vacía debería rechazarse antes de llamar a la API: {rag!r}"
    catalogo = ejecutar_tool("buscar_componentes", {"componente": "GPU", "precio_max": 300})
    if "resultados" not in catalogo:
        return False, f"catálogo: sin resultados para gpu ≤ 300: {catalogo[:120]!r}"

    original = divisas.requests.get
    divisas.requests.get = lambda *a, **k: (_ for _ in ()).throw(ConnectionError("sin red"))
    try:
        api = ejecutar_tool("convertir_divisa", {"cantidad": 100, "origen": "eur", "destino": "USD"})
    finally:
        divisas.requests.get = original
    if "fuente: fallback" not in api:
        return False, f"API: sin red debería usar el fallback local: {api!r}"

    total = ejecutar_tool("calcular_total_build", {"precios": [129.99, 199.99], "presupuesto": 300})
    if "'within_budget': False" not in total or not ejecutar_tool("hora_actual", {}).startswith("20"):
        return False, f"auxiliares incorrectas: {total!r}"

    if not config_grafo.IMAGEN_DEMO_PATH.is_file():
        return False, "falta assets/imagen_demo.jpg"
    fuera = ejecutar_tool("describir_imagen", {"ruta": "config.py"})
    if "solo se pueden leer" not in fuera:
        return False, f"multimodal: debería bloquear rutas fuera de assets/: {fuera!r}"
    return True, "RAG, catálogo, API (fallback), auxiliares y multimodal (ruta) OK"


def _build_graph_ok() -> tuple[bool, str]:
    codigo = inspect.getsource(gmod.build_graph)
    for pieza in ("interrupt_before", "MemorySaver", "add_conditional_edges"):
        if pieza not in codigo:
            return False, f"build_graph debe usar {pieza}"
    app = gmod.build_graph()
    nodos = set(app.get_graph().nodes)
    esperados = {"supervisor", "requisitos", "componentes", "sintetizar", "aplicar"}
    if not esperados <= nodos:
        return False, f"faltan nodos: {esperados - nodos}"
    return True, "compila con MemorySaver + interrupt_before=['aplicar']"


def _hitl_aprobar_ok() -> tuple[bool, str]:
    from src.agent import aprobar_plan, nuevo_thread_id, procesar_turno
    from src.state import crear_estado

    falso = _con_llm_falso()
    tid = nuevo_thread_id()
    estado = procesar_turno(crear_estado(""), "PC gaming 1080p 60 fps, presupuesto de $700", tid)
    if estado.get("error"):
        return False, f"error en procesar_turno: {estado['error']}"
    if not estado.get("pendiente_hitl") or len(estado.get("plan") or []) < 2:
        return False, f"debería pausar con plan ≥2 viñetas (hitl={estado.get('pendiente_hitl')})"
    if not gmod.hay_interrupt(tid):
        return False, "get_state().next debería incluir 'aplicar'"
    tools = estado["traza"][-1]["tools"]
    if not any(t["status"] == "blocked" for t in tools):
        return False, "la tool inventada debería salir como 'blocked' en la traza"
    if not any("fallback" in linea for linea in estado["log"]):
        return False, "el supervisor debería usar el fallback ante una palabra inválida"
    if estado["resumen_presupuesto"].get("dentro") is not True:
        return False, f"resumen_presupuesto inesperado: {estado['resumen_presupuesto']}"

    bloqueado = procesar_turno(estado, "otro pedido", tid)
    if "pendiente" not in bloqueado["respuesta"] or len(bloqueado["traza"]) != len(estado["traza"]):
        return False, "con el grafo pausado no debería aceptarse un mensaje nuevo"

    final = aprobar_plan(tid, True, estado)
    if not final.get("done") or gmod.hay_interrupt(tid):
        return False, "tras aprobar: done=True y sin pausa pendiente"
    return True, f"pausa → aprobar → done ({len(falso.llamadas)} llamadas simuladas)"


def _hitl_rechazar_ok() -> tuple[bool, str]:
    from src.agent import aprobar_plan, nuevo_thread_id, procesar_turno
    from src.state import crear_estado

    _con_llm_falso()
    tid = nuevo_thread_id()
    estado = procesar_turno(crear_estado(""), "PC gaming 1080p, presupuesto de 700 euros", tid)
    estado = aprobar_plan(tid, False, estado, comentario="demasiado caro, como mucho 300 USD")
    if estado.get("done") or estado.get("plan") or estado.get("pendiente_hitl"):
        return False, "tras rechazar: done=False, plan vacío y sin pausa"

    # Mismo thread_id: el checkpointer recuerda el rechazo y su motivo.
    estado = procesar_turno(estado, "Vale, algo más barato", tid)
    historial = gmod.get_app().get_state(gmod.config_hilo(tid)).values.get("historial") or []
    if not any("demasiado caro" in h.get("texto", "") for h in historial):
        return False, "el motivo del rechazo debería quedar en el historial del hilo"
    if not estado.get("pendiente_hitl"):
        return False, "tras rechazar, otro mensaje debería producir un plan nuevo"
    # El presupuesto más reciente (el del motivo) manda: 329.98 > 300 → aviso.
    if estado["preferencias"].get("presupuesto") != 300 or estado["resumen_presupuesto"].get("dentro") is not False:
        return False, f"el presupuesto del motivo debería mandar: {estado['resumen_presupuesto']}"
    if "supera el presupuesto" not in estado.get("respuesta", ""):
        return False, "el plan fuera de presupuesto debería llevar un aviso antes del HITL"
    return True, f"rechazar con motivo → nuevo plan con el presupuesto nuevo ({len(historial)} entradas)"


def _espera_429_ok() -> tuple[bool, str]:
    from src.tools.rag_catalogo import _segundos_espera_429

    if _segundos_espera_429(ValueError("timeout de red")) is not None:
        return False, "un error que no es 429 no debería reintentarse"
    espera = _segundos_espera_429(RuntimeError("429 RESOURCE_EXHAUSTED ... Please retry in 38.08s."))
    if espera is None or not 38 < espera < 40:
        return False, f"debería leer la espera del servidor: {espera}"
    diario = RuntimeError("429 RESOURCE_EXHAUSTED quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier")
    if _segundos_espera_429(diario) is not None:
        return False, "el límite diario no debería reintentarse"
    return True, "reintenta el 429 por minuto; no el diario ni otros errores"


def _parse_plan_ok() -> tuple[bool, str]:
    texto = "**Configuración gaming**\n- CPU: Ryzen 5 — 129.99 USD\n* GPU: RX 6600 — 199.99 USD\nTotal estimado: 329.98 USD"
    plan = gmod._parse_plan(texto)
    if plan != ["CPU: Ryzen 5 — 129.99 USD", "GPU: RX 6600 — 199.99 USD"]:
        return False, f"viñetas mal extraídas: {plan}"
    return True, "un título en negrita no cuenta como viñeta"


def _faltan_datos_ok() -> tuple[bool, str]:
    from src.agent import nuevo_thread_id, procesar_turno
    from src.state import crear_estado

    falso = _con_llm_falso()
    tid = nuevo_thread_id()
    estado = procesar_turno(crear_estado(""), "Quiero armar una PC, ¿qué me recomiendas?", tid)
    if estado.get("pendiente_hitl") or estado.get("plan"):
        return False, "sin datos mínimos no debería haber plan ni pausa HITL"
    if "presupuesto" not in estado.get("respuesta", ""):
        return False, "la respuesta debería pedir el presupuesto"
    if any(r in falso.llamadas for r in ("requisitos", "componentes", "sintetizar")):
        return False, "no debería gastar llamadas al LLM en especialistas"

    # El usuario completa los datos en el MISMO hilo → ahora sí hay plan.
    estado = procesar_turno(estado, "Para jugar, unos 800 dólares", tid)
    if not estado.get("pendiente_hitl"):
        return False, "con los datos completados en el hilo debería proponer plan"
    return True, "pregunta aclaratoria → datos en el siguiente turno → plan"


def _max_iter_ok() -> tuple[bool, str]:
    from src.agent import nuevo_thread_id, procesar_turno
    from src.state import crear_estado

    _con_llm_falso()
    original = config_grafo.MAX_ITER
    config_grafo.MAX_ITER = 2
    try:
        estado = procesar_turno(crear_estado(""), "PC gaming, presupuesto de $700", nuevo_thread_id())
    finally:
        config_grafo.MAX_ITER = original
    if not any("MAX_ITER" in linea for linea in estado.get("log") or []):
        return False, "el log debería mostrar el corte por MAX_ITER"
    if not estado.get("pendiente_hitl"):
        return False, "aunque corte MAX_ITER, debe cerrar con algo que aprobar"
    return True, "corta por MAX_ITER y aun así llega a la pausa HITL"


def _hilos_aislados_ok() -> tuple[bool, str]:
    from src.agent import nuevo_thread_id, procesar_turno
    from src.state import crear_estado

    _con_llm_falso()
    a, b = nuevo_thread_id(), nuevo_thread_id()
    procesar_turno(crear_estado(""), "PC gaming, presupuesto de $700", a)
    if gmod.hay_interrupt(b) or gmod.get_app().get_state(gmod.config_hilo(b)).values:
        return False, "un thread_id nuevo no debería ver el estado de otro"
    return True, "dos thread_id = dos conversaciones"


def _mensaje_vacio_ok() -> tuple[bool, str]:
    from src.agent import procesar_turno

    out = procesar_turno({"traza": []}, "   ", "check-thread")
    if not (out.get("respuesta") or "").strip():
        return False, "procesar_turno con mensaje vacío debe devolver respuesta"
    return True, "mensaje vacío no invoca el grafo"


def main() -> int:
    checks = [
        ("[siguiente] _fallback_siguiente", _fallback_ok),
        ("[siguiente] _eleccion_valida", _eleccion_valida_ok),
        ("[guardrails] preferencias / presupuesto", _guardrails_ok),
        ("[sintetizar] _parse_plan", _parse_plan_ok),
        ("[tools] allowlist", _allowlist_ok),
        ("[tools] 4 categorías fuera del grafo", _tools_aisladas_ok),
        ("[tools] espera ante 429", _espera_429_ok),
        ("[edges] build_graph", _build_graph_ok),
        ("[turno] mensaje vacío", _mensaje_vacio_ok),
        ("[hitl] aprobar", _hitl_aprobar_ok),
        ("[hitl] rechazar + memoria del hilo", _hitl_rechazar_ok),
        ("[turno] faltan datos", _faltan_datos_ok),
        ("[límites] MAX_ITER", _max_iter_ok),
        ("[persistencia] thread_id aislados", _hilos_aislados_ok),
    ]
    ok_all = True
    for nombre, fn in checks:
        try:
            ok, msg = fn()
        except Exception as e:  # noqa: BLE001
            ok, msg = False, f"{type(e).__name__}: {e}"
        print(f"{'[OK]' if ok else '[FAIL]'} {nombre}: {msg}")
        ok_all = ok_all and ok

    print("\nTodos los checks OK. Prueba real: python -m src.cli" if ok_all else "\nHay checks en [FAIL].")
    return 0 if ok_all else 1


if __name__ == "__main__":
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
