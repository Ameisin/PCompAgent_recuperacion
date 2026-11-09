"""Punto único por el que el grafo obtiene sus tools (contrato de clase de src/tools/)."""

from src.tools import TOOLS, ejecutar_tool


def describir_tools() -> str:
    """Lista 'nombre: descripción' para los prompts de los especialistas.

    Se genera a partir de TOOLS, de modo que si el equipo añade o renombra una
    tool los prompts se actualizan solos (no hay nombres fijos en el grafo).
    """
    lineas = []
    for t in TOOLS:
        descripcion = " ".join((t.description or "").split())
        lineas.append(f"- {t.name}: {descripcion}")
    return "\n".join(lineas)


__all__ = ["TOOLS", "ejecutar_tool", "describir_tools"]
