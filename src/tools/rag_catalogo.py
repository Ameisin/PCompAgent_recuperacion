"""Tool RAG: envuelve responder() del RAG completo del PB1 (ChromaDB + Gemini + abstención)."""

import re
import time

from langchain_core.tools import tool

from src import config_grafo
from src.llm import exigir_api_key, limitador


def _segundos_espera_429(error: Exception) -> float | None:
    """Si el error es un 429 POR MINUTO de Gemini, devuelve la espera que pide el servidor.

    Devuelve None (no reintentar) si no es un 429 o si es el límite DIARIO
    (quotaId "...PerDay..."): esperar unos segundos no lo resuelve.
    El mensaje trae "Please retry in 38.08s" o "'retryDelay': '38s'".
    """
    texto = str(error)
    if "429" not in texto and "RESOURCE_EXHAUSTED" not in texto:
        return None
    if "PerDay" in texto:
        return None
    m = re.search(r"retry in ([\d.]+)s", texto) or re.search(r"retryDelay'?:\s*'([\d.]+)s", texto)
    return float(m.group(1)) + 1 if m else 30.0


@tool
def RAG_consultar_catalogo(consulta: str, top_k: int = 5) -> str:
    """Consulta el RAG del proyecto: compatibilidades (socket, tipo de memoria, formato
    de placa y caja), guías de compra/montaje y requisitos de videojuegos. Devuelve una
    respuesta anclada al corpus con sus fuentes, o dice que no tiene la información.
    Para precios exactos por categoría usa buscar_componentes. Ejemplo de consulta:
    'requisitos recomendados de Cyberpunk 2077'.
    """
    # Import diferido: logic arrastra Chroma y el cliente de Gemini; así el
    # grafo se puede compilar y verificar sin cargar el índice.
    from logic import responder

    exigir_api_key()  # sin clave, el RAG del PB1 la pediría por teclado y colgaría el proceso
    # Mismo limitador que el agente si generan con el mismo modelo (misma cuota).
    modelo = config_grafo.RAG_GEMINI_MODEL
    rpm = config_grafo.LLM_RPM if modelo == config_grafo.GEMINI_MODEL else config_grafo.RAG_RPM
    limitador(modelo, rpm).acquire()
    try:
        resultado = responder(consulta, top_k=top_k, modelo=modelo)
    except Exception as e:  # noqa: BLE001
        espera = _segundos_espera_429(e)
        if espera is None:
            raise
        # 429 por minuto: un único reintento tras la espera que indica el servidor.
        time.sleep(min(espera, config_grafo.RAG_ESPERA_MAX_429_S))
        resultado = responder(consulta, top_k=top_k, modelo=modelo)
    if resultado.get("error"):
        return f"Error: {resultado['error']}"
    fuentes = ", ".join(resultado.get("fuentes") or []) or "(sin fuentes)"
    return f"{resultado.get('respuesta') or '(sin respuesta)'}\n\nFuentes: {fuentes}"
