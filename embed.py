"""
Embeddings (EMBED): texto -> vector.

Proveedor conmutable desde config.EMBEDDING_PROVIDER:
  - "gemini"      : client.models.embed_content (google-genai), camino principal del bootcamp.
                    Usa task_type RETRIEVAL_DOCUMENT al indexar y RETRIEVAL_QUERY al consultar
                    (la opción "avanzada" de la live review), y reduce la dimensión a 768.
  - "huggingface" : sentence-transformers en local (sin API key, sin cuota).

Regla de oro: el MISMO proveedor+modelo para indexar y para consultar. La huella del
modelo (config.nombre_modelo_embedding) se guarda en la caché y en la colección Chroma,
y `index.py` se niega a consultar si no coincide.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from langchain_core.documents import Document

import config

logger = logging.getLogger(__name__)

FuncionEmbedding = Callable[[list[str]], list[list[float]]]

# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------
_cliente_gemini = None


def _cliente():
    global _cliente_gemini
    if _cliente_gemini is None:
        from google import genai

        from gemini_auto import configurar_gemini_api_key

        configurar_gemini_api_key()
        _cliente_gemini = genai.Client()
    return _cliente_gemini


def _embed_gemini_lote(textos: list[str], tipo_tarea: str) -> list[list[float]]:
    from google.genai import types

    cliente = _cliente()
    for intento in range(1, config.EMBED_MAX_REINTENTOS + 1):
        try:
            result = cliente.models.embed_content(
                model=config.DEFAULT_GEMINI_EMBEDDING_MODEL,
                contents=cast(Any, textos),
                config=types.EmbedContentConfig(
                    task_type=tipo_tarea,
                    output_dimensionality=config.DEFAULT_GEMINI_EMBEDDING_DIM,
                ),
            )
            embeddings = result.embeddings or []
            vectores: list[list[float]] = []
            for embedding in embeddings:
                values = embedding.values
                if values is not None:
                    vectores.append(list(values))
            return vectores
        except Exception as exc:  # noqa: BLE001 - la API lanza tipos distintos según el error
            mensaje = str(exc)
            transitorio = any(s in mensaje for s in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "timeout"))
            if not transitorio or intento == config.EMBED_MAX_REINTENTOS:
                raise
            espera = config.EMBED_ESPERA_BASE_S * (2 ** (intento - 1))
            logger.warning("Gemini embed: error transitorio (intento %d/%d), reintento en %.0f s: %s",
                           intento, config.EMBED_MAX_REINTENTOS, espera, mensaje[:120])
            time.sleep(espera)
    raise RuntimeError("No se pudo generar el embedding")  # inalcanzable


def _embed_gemini(textos: list[str], tipo_tarea: str) -> list[list[float]]:
    vectores: list[list[float]] = []
    total = len(textos)
    for inicio in range(0, total, config.EMBED_BATCH_SIZE):
        lote = textos[inicio:inicio + config.EMBED_BATCH_SIZE]
        vectores.extend(_embed_gemini_lote(lote, tipo_tarea))
        if total > config.EMBED_BATCH_SIZE:
            logger.info("  embeddings %d/%d", min(inicio + len(lote), total), total)
    return vectores


# ---------------------------------------------------------------------------
# Hugging Face local
# ---------------------------------------------------------------------------
_modelo_hf = None


def _modelo_sentence_transformers():
    global _modelo_hf
    if _modelo_hf is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Cargando modelo local %s (la primera vez descarga los pesos)", config.HF_EMBEDDING_MODEL)
        _modelo_hf = SentenceTransformer(config.HF_EMBEDDING_MODEL)
    return _modelo_hf


def _embed_huggingface(textos: list[str]) -> list[list[float]]:
    modelo = _modelo_sentence_transformers()
    vectores = modelo.encode(textos, normalize_embeddings=True, batch_size=64, show_progress_bar=len(textos) > 200)
    return [list(map(float, v)) for v in vectores]


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------
def embed_textos(textos: list[str], tipo_tarea: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    if not textos:
        return []
    if config.EMBEDDING_PROVIDER == "gemini":
        return _embed_gemini(textos, tipo_tarea)
    if config.EMBEDDING_PROVIDER == "huggingface":
        return _embed_huggingface(textos)
    raise ValueError(f"EMBEDDING_PROVIDER no soportado: {config.EMBEDDING_PROVIDER!r}")


def embed_documentos(textos: list[str]) -> list[list[float]]:
    """Vectoriza chunks para indexar."""
    logger.info("Generando %d embeddings con %s", len(textos), config.nombre_modelo_embedding())
    return embed_textos(textos, "RETRIEVAL_DOCUMENT")


def embed_consulta(texto: str) -> list[float]:
    """Vectoriza la pregunta del usuario (mismo modelo, task_type de consulta)."""
    return embed_textos([texto], "RETRIEVAL_QUERY")[0]


# ---------------------------------------------------------------------------
# Caché en output/embeddings.json (formato de la live review + huella del modelo)
# ---------------------------------------------------------------------------
def _huella_textos(chunks: list[Document]) -> str:
    h = hashlib.sha256()
    for c in chunks:
        h.update(c.page_content.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def guardar_embeddings_json(chunks: list[Document], vectores: list[list[float]], ruta: Path | None = None) -> None:
    ruta = ruta or config.EMBEDDINGS_JSON
    ruta.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "embedding_model": config.nombre_modelo_embedding(),
        "dimensiones": len(vectores[0]) if vectores else 0,
        "huella_textos": _huella_textos(chunks),
        "total": len(chunks),
        "items": [
            {"text": c.page_content, "vector": v, "metadata": dict(c.metadata)}
            for c, v in zip(chunks, vectores)
        ],
    }
    ruta.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    logger.info("Embeddings guardados en %s (%d vectores de %d dimensiones)",
                config.ruta_corta(ruta), payload["total"], payload["dimensiones"])


def cargar_embeddings_cache(chunks: list[Document], ruta: Path | None = None) -> list[list[float]] | None:
    """Devuelve los vectores cacheados solo si el modelo y los textos son exactamente los mismos."""
    ruta = ruta or config.EMBEDDINGS_JSON
    if not ruta.exists():
        return None
    try:
        payload = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if payload.get("embedding_model") != config.nombre_modelo_embedding():
        logger.info("Caché de embeddings descartada: modelo distinto (%s)", payload.get("embedding_model"))
        return None
    if payload.get("huella_textos") != _huella_textos(chunks):
        logger.info("Caché de embeddings descartada: los chunks han cambiado")
        return None
    return [item["vector"] for item in payload["items"]]
