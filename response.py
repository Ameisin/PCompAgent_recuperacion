from time import time

from config import TOP_K
from retrieve import recuperar


def response(pregunta: str, top_k: int | None = None, modelo: str | None = None) -> dict:
    """
    API interna del RAG: retrieval + generación + métricas.
    """

    start = time()

    # 1) Retrieval
    k = top_k if top_k is not None else TOP_K
    respuesta = recuperar(pregunta, top_k=k)

    # 2) Métricas
    elapsed_ms = int((time() - start) * 1000)

    return {
        "respuesta": respuesta,
        "chunks": [
            {
                "texto": ch["text"],
                "source": ch["metadata"].get("source", "?"),
                "distance": ch["distance"]
            }
            for ch in respuesta
        ],
        "modelo": modelo if modelo else "gemini-1.5-flash",
        "k": k,
        "num_chunks": len(respuesta),
        "tiempo_ms": elapsed_ms
    }
