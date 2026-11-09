"""Tool API externa: convertir_divisa con Frankfurter (BCE, sin clave) + fallback JSON local.

El catálogo está en USD; el usuario suele pensar en euros. Idea de la tool del
compañero (tools/agent_rag_tools.py::convert_currency) con el fallback que pide el PB2.
"""

import json

import requests
from langchain_core.tools import tool

from src import config_grafo


def _tasas_fallback(origen: str) -> tuple[dict, str]:
    """Tasas desde el JSON local (base EUR), recalculadas para la moneda de origen."""
    data = json.loads(config_grafo.DIVISAS_FALLBACK_PATH.read_text(encoding="utf-8"))
    tasas = {"EUR": 1.0, **data["rates"]}
    if origen not in tasas:
        raise ValueError(f"moneda '{origen}' no está en el fallback")
    return {m: v / tasas[origen] for m, v in tasas.items()}, data.get("date", "?")


@tool
def convertir_divisa(cantidad: float, origen: str, destino: str) -> str:
    """Convierte una cantidad entre monedas (códigos ISO de 3 letras, p. ej. EUR, USD)
    con el tipo de cambio actual del BCE. Úsala si el usuario da el presupuesto en euros:
    los precios del catálogo están en USD.
    """
    try:
        r = requests.get(
            config_grafo.DIVISAS_URL,
            params={"amount": cantidad, "from": origen, "to": destino},
            timeout=config_grafo.HTTP_TIMEOUT_SECONDS,
        )
        r.raise_for_status()
        data = r.json()
        valor, fecha, fuente = data["rates"][destino], data["date"], "api"
    except Exception:  # noqa: BLE001 (sin red o API caída: fallback local)
        tasas, fecha = _tasas_fallback(origen)
        if destino not in tasas:
            return f"Error: moneda '{destino}' no disponible."
        valor, fuente = round(cantidad * tasas[destino], 2), "fallback"
    return f"{cantidad} {origen} = {valor} {destino} (fecha: {fecha}, fuente: {fuente})"
