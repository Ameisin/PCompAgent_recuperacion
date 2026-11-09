"""
Chunking (CHUNK): fragmenta los documentos y añade metadatos de trazabilidad.

Estrategia diferenciada por tipo de documento:
  - "guia" (Markdown/PDF largos)  -> RecursiveCharacterTextSplitter(CHUNK_SIZE, CHUNK_OVERLAP)
  - "componente" / "videojuego"    -> NO se fragmentan: cada fila del CSV ya es una unidad
                                      semántica completa (~200-400 caracteres). Partirla
                                      separaría el nombre del producto de sus características.
"""

from __future__ import annotations

import logging

import config
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def crear_splitter(chunk_size: int = config.CHUNK_SIZE, chunk_overlap: int = config.CHUNK_OVERLAP):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def _fragmentar_por_secciones(documentos: list[Document], splitter) -> list[Document]: ## 
    """Estrategia "markdown_headers": divide primero por encabezados (#, ##, ###) y luego,
    solo si una sección supera CHUNK_SIZE, aplica el splitter recursivo dentro de ella.
    Cada chunk empieza con su ruta de sección, de modo que el embedding 
    conserva el contexto aunque el párrafo sea corto o una tabla."""
    from langchain_text_splitters import MarkdownHeaderTextSplitter

    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "titulo"), ("##", "seccion"), ("###", "subseccion")],
        strip_headers=True,
    )
    resultado: list[Document] = []
    for doc in documentos:
        es_markdown = str(doc.metadata.get("source", "")).lower().endswith(".md")
        secciones = md_splitter.split_text(doc.page_content) if es_markdown else [doc]
        for seccion in secciones:
            ruta = " > ".join(
                seccion.metadata[k] for k in ("titulo", "seccion", "subseccion") if seccion.metadata.get(k)
            )
            meta = {**doc.metadata, **{k: v for k, v in seccion.metadata.items() if k in ("seccion", "subseccion")}}
            partes = splitter.split_text(seccion.page_content)
            for parte in partes:
                texto = f"[{ruta}]\n{parte}" if ruta else parte
                resultado.append(Document(page_content=texto, metadata=dict(meta)))
    return resultado


def enriquecer_metadata(chunks: list[Document]) -> list[Document]: ## Copia los metadatos del documento padre y añade chunk_index / chunk_size.
    enriquecidos = []
    for i, chunk in enumerate(chunks):
        meta = dict(chunk.metadata)
        meta["chunk_index"] = i
        meta["chunk_size"] = len(chunk.page_content)
        enriquecidos.append(Document(page_content=chunk.page_content, metadata=meta))
    return enriquecidos


def fragmentar_documentos(
    documentos: list[Document],
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> list[Document]:
    fragmentables = [d for d in documentos if d.metadata.get("tipo") in config.TIPOS_DOC_FRAGMENTABLES]
    atomicos = [d for d in documentos if d.metadata.get("tipo") not in config.TIPOS_DOC_FRAGMENTABLES]

    splitter = crear_splitter(chunk_size, chunk_overlap)
    if config.ESTRATEGIA_CHUNKING == "markdown_headers":
        chunks_guias = _fragmentar_por_secciones(fragmentables, splitter)
    else:
        chunks_guias = splitter.split_documents(fragmentables) if fragmentables else []
    ## Índice del chunk dentro de su propio documento (útil para citar "guía, fragmento 3")
    contador: dict[str, int] = {}
    for c in chunks_guias:
        clave = c.metadata.get("source", "")
        contador[clave] = contador.get(clave, 0) + 1
        c.metadata["fragmento"] = contador[clave]

    logger.info("  Guías: %d documentos -> %d chunks (chunk_size=%d, overlap=%d)",
                len(fragmentables), len(chunks_guias), chunk_size, chunk_overlap)
    logger.info("  Filas CSV (atómicas, sin fragmentar): %d", len(atomicos))

    chunks = enriquecer_metadata(chunks_guias + atomicos)
    return aplicar_limite(chunks, config.MAX_CHUNKS)


def aplicar_limite(chunks: list[Document], max_chunks: int | None) -> list[Document]: ## MAX_CHUNKS global (None = sin límite). Se aplica *después* de mezclar guías y CSV para que, incluso en pruebas rápidas, el índice contenga ambos formatos.
    if max_chunks is None or len(chunks) <= max_chunks:
        return chunks
    logger.warning("  MAX_CHUNKS=%d: se indexan solo %d de %d chunks", max_chunks, max_chunks, len(chunks))
    return chunks[:max_chunks]


def resumen_chunks(chunks: list[Document]) -> dict: ## Estadísticas para el log y el informe (tamaños por tipo).
    por_tipo: dict[str, list[int]] = {}
    for c in chunks:
        por_tipo.setdefault(c.metadata.get("tipo", "?"), []).append(len(c.page_content))
    return {
        tipo: {"n": len(v), "min": min(v), "max": max(v), "media": round(sum(v) / len(v))}
        for tipo, v in por_tipo.items()
    }
