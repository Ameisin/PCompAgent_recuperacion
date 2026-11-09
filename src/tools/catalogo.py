"""Tool: buscar_componentes, búsqueda por categoría y precio en los CSV del catálogo.

Envuelve buscar_precio() de tools/tools.py (rama feature/tools-rag) como @tool.
Da precios exactos de TODAS las categorías aunque el índice vectorial esté incompleto.
"""

from langchain_core.tools import tool

from tools.tools import buscar_precio


@tool
def buscar_componentes(componente: str, precio_min: float = 0, precio_max: float | None = None) -> str:
    """Busca productos REALES del catálogo por categoría y rango de precio (USD), de más
    barato a más caro (máx. 10), con sus especificaciones (socket, memoria, formato,
    chipset, potencia...). Categorías: cpu, gpu, placa_base, ram, almacenamiento,
    fuente, caja, disipador, ventilador, pasta_termica, tarjeta_sonido, tarjeta_red.
    Pon un precio_min cercano al reparto del presupuesto para no recibir solo las piezas
    más baratas.
    """
    return str(buscar_precio(componente, precio_min, precio_max))
