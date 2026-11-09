"""Tools auxiliares deterministas (ni RAG ni API): total de la build y hora actual."""

from datetime import datetime

from langchain_core.tools import tool

from tools.tools import calculate_build_total


@tool
def calcular_total_build(precios: list[float], presupuesto: float | None = None) -> str:
    """Suma los precios (USD) de las piezas elegidas y dice cuánto queda o cuánto se pasa
    respecto al presupuesto. Úsala antes de cerrar una configuración.
    """
    # Reutiliza calculate_build_total de tools/tools.py (rama feature/tools-rag).
    items = [{"name": f"pieza {i}", "price": p} for i, p in enumerate(precios, start=1)]
    return str(calculate_build_total(items, budget=presupuesto))


@tool
def hora_actual() -> str:
    """Devuelve la fecha y hora local actuales en formato ISO."""
    return datetime.now().isoformat(timespec="seconds")
