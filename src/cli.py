"""CLI del agente multiagente (cliente del grafo) de PCompAgent.

Se ejecuta desde la raíz del proyecto:
  python -m src.cli                                   # demo (HITL auto-aprobado)
  python -m src.cli --sin-auto-aprobar                # demo que se queda en pausa HITL
  python -m src.cli --mensaje "PC gaming 1440p, $1200"  # demo con otro pedido
  python -m src.cli --interactivo                     # chat; con plan pendiente: aprobar / rechazar
  python -m src.cli --max-turns 3 --max-steps 1       # límites
  python -m src.cli --supervisor-reglas               # supervisor sin LLM (ahorra cuota)
"""

import argparse
import json
import sys

from src import config_grafo
from src.agent import aprobar_plan, nuevo_thread_id, procesar_turno, run_demo
from src.state import crear_estado

COMANDOS_APROBAR = {"aprobar", "approve", "si", "sí", "yes"}
COMANDOS_RECHAZAR = {"rechazar", "reject", "no"}
COMANDOS_SALIR = {"salir", "exit", "quit"}


def _imprimir_turno(estado: dict) -> None:
    print("Agente:", estado.get("respuesta") or "(sin respuesta)")
    if estado.get("plan"):
        print("Plan:")
        for item in estado["plan"]:
            print(f"  - {item}")
    resumen = estado.get("resumen_presupuesto") or {}
    if resumen.get("total") is not None:
        print(
            f"Suma de precios: {resumen['total']} | presupuesto: {resumen.get('presupuesto')} "
            f"| dentro: {resumen.get('dentro')}"
        )
    ultimo = (estado.get("traza") or [{}])[-1]
    if ultimo.get("log"):
        print("Log:", ultimo["log"])
    if ultimo.get("tools"):
        print("Tools:", [(t["tool"], t["status"]) for t in ultimo["tools"]])
    print(
        "done:",
        estado.get("done"),
        "| hitl:",
        estado.get("pendiente_hitl"),
        "| error:",
        estado.get("error"),
    )
    print()


def _interactivo(max_turns: int, max_steps: int) -> dict:
    estado = crear_estado("")
    tid = nuevo_thread_id()
    print(f"Modo interactivo | thread_id={tid}")
    print("Vacío o 'salir' para terminar. Si hay HITL: 'aprobar' / 'rechazar'.\n")
    # El tope cuenta mensajes y decisiones HITL; procesar_turno aplica además max_turns.
    for _ in range(max_turns * 2):
        if estado.get("pendiente_hitl"):
            print("HITL: plan pendiente. Escribe aprobar / rechazar")
        mensaje = input("Tú: ").strip()
        if not mensaje or mensaje.lower() in COMANDOS_SALIR:
            break
        if mensaje.lower() in COMANDOS_APROBAR | COMANDOS_RECHAZAR:
            if not estado.get("pendiente_hitl"):
                print("(No hay plan pendiente)")
                continue
            aprobado = mensaje.lower() in COMANDOS_APROBAR
            comentario = "" if aprobado else input("Motivo del rechazo (opcional): ").strip()
            estado = aprobar_plan(tid, aprobado, estado, comentario=comentario)
        else:
            estado = procesar_turno(estado, mensaje, tid, max_steps=max_steps, max_turns=max_turns)
        _imprimir_turno(estado)
        if estado.get("done") or estado.get("error"):
            break
    estado["thread_id"] = tid
    return estado


def _resumen(estado: dict, max_turns: int, max_steps: int) -> None:
    traza = estado.get("traza") or []
    print("--- resumen ---")
    print(
        f"turnos: {len(traza)}/{max_turns} | done: {estado.get('done')} "
        f"| hitl: {estado.get('pendiente_hitl')} | error: {bool(estado.get('error'))}"
    )
    print(f"thread_id: {estado.get('thread_id')}")
    print(f"max_steps: {max_steps} | MAX_ITER: {config_grafo.MAX_ITER} | modelo: {config_grafo.GEMINI_MODEL}")
    print("log:", estado.get("log"))
    print("---------------")


def main() -> None:
    # La consola de Windows puede no ser UTF-8: evita que un acento tumbe la CLI.
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Multiagente PCompAgent + LangGraph")
    parser.add_argument("--interactivo", action="store_true")
    parser.add_argument("--max-turns", type=int, default=config_grafo.MAX_TURNS_DEFAULT)
    parser.add_argument("--max-steps", type=int, default=config_grafo.MAX_STEPS_DEFAULT)
    parser.add_argument("--mensaje", help="Pedido de la demo (por defecto, config_grafo.DEMO_MENSAJES)")
    parser.add_argument(
        "--sin-auto-aprobar",
        action="store_true",
        help="En demo, no auto-aprueba el plan HITL",
    )
    parser.add_argument(
        "--supervisor-reglas",
        action="store_true",
        help="El supervisor enruta solo con reglas Python (sin llamar al LLM)",
    )
    args = parser.parse_args()

    if args.supervisor_reglas:
        config_grafo.SUPERVISOR_USA_LLM = False

    if args.interactivo:
        resultado = _interactivo(args.max_turns, args.max_steps)
    else:
        resultado = run_demo(
            mensajes=[args.mensaje] if args.mensaje else None,
            max_turns=args.max_turns,
            max_steps=args.max_steps,
            auto_aprobar=not args.sin_auto_aprobar,
        )

    _resumen(resultado, args.max_turns, args.max_steps)
    print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
