"""Estado de producto (UI / CLI) y helpers.

Hay dos estados distintos (idea de clase, Sprint 13):
  - EstadoGrafo (src/graph.py): lo que leen y escriben los nodos; lo guarda el
    checkpointer por thread_id.
  - Estado de producto (este módulo): lo que ven CLI y Streamlit (respuesta,
    plan, flags HITL, traza por turno). Se rellena a partir de la salida del grafo.

crear_estado: plantilla visible en Streamlit / JSON de la CLI.
estado_desde_grafo: copia al estado de producto los campos que salen del grafo.
"""

import copy
from typing import Any

# Campos del grafo que se copian tal cual al estado de producto.
CAMPOS_DEL_GRAFO = (
    "pedido",
    "preferencias",
    "faltan_datos",
    "notas_requisitos",
    "notas_componentes",
    "respuesta",
    "plan",
    "resumen_presupuesto",
    "siguiente",
    "iteracion",
    "log",
    "traza_tools",
    "done",
    "plan_aprobado",
    "pendiente_hitl",
)


def crear_estado(pedido: str = "") -> dict[str, Any]:
    """Plantilla visible en Streamlit / resumen CLI."""
    return {
        "objetivo": "Recomendar una configuración de PC (multiagente LangGraph)",
        "pedido_original": pedido,
        "pedido": pedido,
        "preferencias": {
            "presupuesto": None,
            "usos": [],
            "categorias": [],
            "pc_completo": True,
        },
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
        "done": False,
        "error": None,
        "pendiente_hitl": False,
        "plan_aprobado": False,
        "thread_id": None,
        "traza": [],  # una entrada por turno (mensaje o decisión HITL)
    }


def estado_desde_grafo(resultado: dict[str, Any], base: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fusiona la salida del grafo sobre el estado de producto (para la UI)."""
    nuevo = copy.deepcopy(base) if base else crear_estado()
    for clave in CAMPOS_DEL_GRAFO:
        if clave in resultado:
            nuevo[clave] = copy.deepcopy(resultado[clave])
    if resultado.get("pedido") and not nuevo.get("pedido_original"):
        nuevo["pedido_original"] = resultado["pedido"]
    return nuevo
