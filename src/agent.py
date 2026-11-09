"""Orquestación: procesar_turno + HITL (interrupt_before aplicar).

Contrato para los clientes (CLI y Streamlit), el mismo que en clase:

    estado = crear_estado("")
    tid = nuevo_thread_id()
    estado = procesar_turno(estado, mensaje, tid, max_steps=...)
    if estado["pendiente_hitl"]:
        estado = aprobar_plan(tid, True | False, estado, comentario="...")

Los clientes solo pintan el estado de producto; la lógica vive en el grafo.
"""

import uuid
from typing import Any

from src import config_grafo
from src.graph import (
    config_hilo,
    estado_inicial_grafo,
    get_app,
    hay_interrupt,
)
from src.state import crear_estado, estado_desde_grafo


def _marcar_hitl(estado: dict[str, Any], thread_id: str) -> dict[str, Any]:
    """Si el grafo está pausado ante aplicar, marca pendiente_hitl para la UI."""
    pendiente = hay_interrupt(thread_id)
    estado = dict(estado)
    estado["pendiente_hitl"] = pendiente
    if pendiente:
        estado["done"] = False
        resp = (estado.get("respuesta") or "").rstrip()
        aviso = "\n\n_(Plan listo: aprueba o rechaza antes de cerrar.)_"
        if "aprueba o rechaza" not in resp.lower():
            estado["respuesta"] = resp + aviso
    return estado


def _longitud_actual(thread_id: str, campo: str) -> int:
    """Nº de elementos de un campo acumulado (log / traza_tools) en el checkpoint.

    Esos campos crecen durante todo el hilo; sabiendo su longitud antes del
    turno, la traza de producto guarda solo lo que pasó en ESTE turno.
    """
    valores = get_app().get_state(config_hilo(thread_id)).values or {}
    return len(valores.get(campo) or [])


def _respuesta_sin_invocar(estado: dict[str, Any], texto: str) -> dict[str, Any]:
    nuevo = dict(estado)
    nuevo["respuesta"] = texto
    return nuevo


def procesar_turno(
    estado: dict[str, Any],
    mensaje: str,
    thread_id: str,
    max_steps: int | None = None,
    max_turns: int | None = None,
) -> dict[str, Any]:
    """Un mensaje de usuario → un invoke del grafo multiagente.

    Puede terminar en pausa HITL (antes de aplicar). El mismo thread_id
    reutiliza el checkpointer MemorySaver.
    """
    mensaje = (mensaje or "").strip()
    if not mensaje:
        return _respuesta_sin_invocar(
            estado, "Escribe un mensaje (uso, presupuesto, juegos o pieza que buscas…)."
        )
    if len(mensaje) > config_grafo.LONGITUD_MAX_MENSAJE:
        return _respuesta_sin_invocar(
            estado, f"El mensaje es demasiado largo (máx. {config_grafo.LONGITUD_MAX_MENSAJE} caracteres)."
        )

    # Límites y guardas decididos en Python, antes de gastar llamadas al modelo.
    turnos_usuario = sum(1 for t in estado.get("traza") or [] if not str(t.get("mensaje", "")).startswith("HITL:"))
    if max_turns is not None and turnos_usuario >= max_turns:
        return _respuesta_sin_invocar(
            estado, f"Se ha alcanzado max_turns ({max_turns}). Empieza una nueva conversación."
        )
    if estado.get("done"):
        return _respuesta_sin_invocar(
            estado, "Esta conversación ya terminó con un plan aprobado. Empieza una nueva conversación."
        )
    if hay_interrupt(thread_id):
        # Con el grafo pausado no se manda otro pedido: hay que reanudar (aprobar_plan).
        return _respuesta_sin_invocar(
            estado, "Hay un plan pendiente de aprobación: apruébalo o recházalo antes de seguir."
        )

    app = get_app()
    cfg = config_hilo(thread_id)
    n = len(estado.get("traza") or []) + 1

    try:
        log_antes = _longitud_actual(thread_id, "log")
        tools_antes = _longitud_actual(thread_id, "traza_tools")
        inicial = estado_inicial_grafo(mensaje, max_steps=max_steps)
        resultado = app.invoke(inicial, cfg)
        nuevo = estado_desde_grafo(resultado, estado)
        nuevo["error"] = None
        nuevo["thread_id"] = thread_id
        if not nuevo.get("pedido_original"):
            nuevo["pedido_original"] = mensaje
        nuevo = _marcar_hitl(nuevo, thread_id)
        nuevo.setdefault("traza", []).append(
            {
                "turno": n,
                "mensaje": mensaje,
                "status": "ok",
                "done": nuevo.get("done"),
                "pendiente_hitl": nuevo.get("pendiente_hitl"),
                "faltan_datos": list(resultado.get("faltan_datos") or []),
                "log": list((resultado.get("log") or [])[log_antes:]),
                "tools": list((resultado.get("traza_tools") or [])[tools_antes:]),
            }
        )
        return nuevo
    except Exception as e:  # noqa: BLE001
        nuevo = dict(estado)
        nuevo["error"] = str(e)
        nuevo["respuesta"] = (
            "No he podido continuar por un error técnico. "
            "Revisa la API key, la cuota de Gemini o que el índice del RAG exista."
        )
        nuevo.setdefault("traza", []).append(
            {
                "turno": n,
                "mensaje": mensaje,
                "status": "error",
                "detail": str(e),
                "tools": [],
            }
        )
        return nuevo


def aprobar_plan(
    thread_id: str,
    aprobado: bool,
    estado: dict[str, Any],
    comentario: str = "",
) -> dict[str, Any]:
    """HITL: guarda la decisión en el checkpoint y reanuda el nodo aplicar.

    1) update_state(plan_aprobado=..., comentario_humano=...)
    2) invoke(None) → continúa desde interrupt_before sin input nuevo

    El comentario (opcional) es el motivo del rechazo: queda en el historial
    del hilo para que el siguiente turno proponga algo distinto.
    """
    app = get_app()
    cfg = config_hilo(thread_id)
    if not hay_interrupt(thread_id):
        return _respuesta_sin_invocar(estado, "No hay plan pendiente de aprobación.")

    try:
        log_antes = _longitud_actual(thread_id, "log")
        app.update_state(
            cfg,
            {"plan_aprobado": bool(aprobado), "comentario_humano": (comentario or "").strip()},
        )
        resultado = app.invoke(None, cfg)
        nuevo = estado_desde_grafo(resultado, estado)
        nuevo["pendiente_hitl"] = False
        nuevo["error"] = None
        nuevo.setdefault("traza", []).append(
            {
                "turno": len(estado.get("traza") or []) + 1,
                "mensaje": "HITL:" + ("aprobar" if aprobado else "rechazar"),
                "comentario": (comentario or "").strip(),
                "status": "ok",
                "done": nuevo.get("done"),
                "pendiente_hitl": False,
                "log": list((resultado.get("log") or [])[log_antes:]),
                "tools": [],
            }
        )
        return nuevo
    except Exception as e:  # noqa: BLE001
        nuevo = dict(estado)
        nuevo["error"] = str(e)
        nuevo["respuesta"] = "No he podido aplicar la decisión por un error técnico."
        return nuevo


def nuevo_thread_id() -> str:
    return f"pc-{uuid.uuid4().hex[:8]}"


def historial_checkpoints(thread_id: str, limite: int = 20) -> list[dict[str, Any]]:
    """Fotos del hilo (más reciente primero): auditoría de qué sabía el agente y cuándo.

    get_state_history no llama al modelo; sirve para el expander de debug.
    """
    fotos = []
    for snap in get_app().get_state_history(config_hilo(thread_id)):
        valores = snap.values or {}
        fotos.append(
            {
                "next": list(snap.next or ()),
                "iteracion": valores.get("iteracion"),
                "siguiente": valores.get("siguiente"),
                "pendiente_hitl": valores.get("pendiente_hitl"),
                "done": valores.get("done"),
            }
        )
        if len(fotos) >= limite:
            break
    return fotos


def run_demo(
    mensajes: list[str] | None = None,
    max_turns: int | None = None,
    max_steps: int | None = None,
    auto_aprobar: bool = True,
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Demo CLI: pedido(s) → posible HITL (auto-aprobado si auto_aprobar=True)."""
    msgs = list(mensajes) if mensajes is not None else list(config_grafo.DEMO_MENSAJES)
    limit = max_turns if max_turns is not None else config_grafo.MAX_TURNS_DEFAULT
    tid = thread_id or nuevo_thread_id()
    estado = crear_estado(msgs[0] if msgs else "")

    for mensaje in msgs[:limit]:
        if estado.get("done") or estado.get("error"):
            break
        estado = procesar_turno(estado, mensaje, tid, max_steps=max_steps)
        if estado.get("pendiente_hitl") and auto_aprobar:
            estado = aprobar_plan(tid, True, estado)

    estado["thread_id"] = tid
    return estado
