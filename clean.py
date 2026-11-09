"""
Limpieza y normalización (CLEAN): mínimo viable, sin reescribir contenido.
Vive entre load y chunk; si algo falla en la limpieza se depura aquí sin tocar
loaders ni splitters.
"""

from __future__ import annotations

import logging
import re

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def unir_guiones_de_linea(texto: str) -> str: ## Cuando en un PDF se encuentran palabras cortadas por un cambio de línea, por ejemplo: 'compati-\\nbilidad' -> 'compatibilidad' (típico de PDFs exportados).
    return re.sub(r"(\w)-\n(\w)", r"\1\2", texto)


def normalizar_texto(texto: str) -> str: ## Espacios, saltos de línea y strip. No pasa a minúsculas ni quita puntuación: los nombres de producto (RTX 4070 Ti, AM5, DDR5-6000) deben conservarse.
    if not texto:
        return ""
    t = texto.replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace(" ", " ")                 ## espacio duro (HTML/PDF)
    t = unir_guiones_de_linea(t)
    t = re.sub(r"\n{3,}", "\n\n", t)             ## conserva párrafos
    t = re.sub(r"[ \t]+", " ", t)                ## colapsa espacios/tabs
    t = "\n".join(linea.strip() for linea in t.split("\n"))
    return t.strip()


def limpiar_documentos(documentos: list[Document]) -> list[Document]: ## Devuelve nuevos Document con el texto normalizado; omite los vacíos.
    limpios: list[Document] = []
    omitidos = 0
    for doc in documentos:
        contenido = normalizar_texto(doc.page_content)
        if not contenido:
            omitidos += 1
            continue
        limpios.append(Document(page_content=contenido, metadata=dict(doc.metadata)))
    if omitidos:
        logger.info("  Documentos vacíos omitidos tras limpiar: %d", omitidos)
    return limpios
