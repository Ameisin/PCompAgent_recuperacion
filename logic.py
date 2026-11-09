"""Orquestación online RAG 

De aqui sacamos la respuesta del LLM y los demas stats.
"""

import time
from pathlib import Path

from context import formatear_contexto
from generate_rep import generar_respuesta
from prompt import build_rag_prompt
from retrieve import recuperar

# ---------------------------------------------------------------------------
# EXTRAIDO DE LAS FUENTES DE INFROMACION 
# ---------------------------------------------------------------------------


def _extraer_fuentes(chunks: list[dict]) -> list[str]:
    fuentes: list[str] = []
    vistos: set[str] = set()
    for chunk in chunks:
        source = chunk.get("metadata", {}).get("source", "?")
        nombre = Path(str(source)).name
        if nombre not in vistos:
            vistos.add(nombre)
            fuentes.append(nombre)
    return fuentes




# ---------------------------------------------------------------------------
# RESPUESTA DEL LLM
# ---------------------------------------------------------------------------

# En este metodo sacamos las respuesta de gemini con todos los limitantes que hemos puesto.

def responder(pregunta: str, top_k: int | None = None, modelo: str | None = None, temperatura: float | None = None, dimension_embedding: int | None = None) -> dict:
    start_time = int(time.time() * 1000)
    """Pipeline: retrieve → prompt → generate."""
    inicio = time.perf_counter()

    if not (pregunta or "").strip():
        return {
            "respuesta": "",
            "contexto": "",
            "chunks": [],
            "fuentes": [],
            "error": "La pregunta no puede estar vacía.",
            "tiempo_ms": 0,
        }

    chunks = recuperar(pregunta.strip(), top_k=top_k)
    contexto = formatear_contexto(chunks)
    prompt = build_rag_prompt(contexto, pregunta.strip())
    respuesta = generar_respuesta(prompt, modelo=modelo, temperatura=temperatura)

    return {
        "respuesta": respuesta,
        "contexto": contexto,
        "chunks": chunks,
        "fuentes": _extraer_fuentes(chunks),
        "error": None,
        "tiempo_ms": int(time.time() * 1000) - start_time
    }
