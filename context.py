"""Formateo del contexto recuperado """

from pathlib import Path


def _nombre_fuente(metadata: dict) -> str:
    source = metadata.get("source", "desconocido")
    return Path(str(source)).name


def formatear_contexto(chunks: list[dict], incluir_distancia: bool = True) -> str:
    """Concatena chunks con delimitadores, fuente y distancia opcional."""
    if not chunks:
        return "(sin fragmentos recuperados)"

    partes: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        fuente = _nombre_fuente(meta)
        cabecera = f"--- Fragmento {i}"
        if incluir_distancia and chunk.get("distance") is not None:
            cabecera += f" (distancia={chunk['distance']:.4f})"
        cabecera += f" ---\nFuente: {fuente}"
        texto = chunk.get("text", "").strip()
        partes.append(f"{cabecera}\n{texto}")

    return "\n\n".join(partes)


def imprimir_contexto(chunks: list[dict]) -> None:
    """Muestra en consola el contexto que usaría un LLM en Sprint 10."""
    print("\n--- Contexto recuperado ---")
    print(formatear_contexto(chunks))
