"""Retriever — Sprint 9 (Fase 2): pregunta → top-K chunks desde ChromaDB.

Objetivo didáctico
------------------
Ya tienes un índice en Chroma (Fase 1). Ahora, dada una pregunta en lenguaje
natural, recuperas los K fragmentos más parecidos semánticamente.

Flujo online (esto es el “motor” de un RAG, sin generación todavía):
  1. Embeddear la pregunta con el MISMO modelo que el índice (Gemini).
  2. collection.query() busca los vectores más cercanos (distancia coseno).
  3. Devolver texto + metadata + distance de cada hit.

"""

from google import genai
from config import COLLECTION_NAME, TOP_K
from embed import embed_consulta
from gemini_auto import configurar_gemini_api_key
from index import obtener_cliente_chroma, obtener_coleccion


def _log_retrieval(pregunta: str, top_k: int) -> None:
    """Traza mínima para depurar: qué preguntaste y con qué K."""
    print(f'\n[RETRIEVAL] query="{pregunta}"')
    print(f"[RETRIEVAL] top_k={top_k} collection={COLLECTION_NAME}")


def _resultados_a_chunks(results: dict) -> list[dict]:
    """Convierte la respuesta anidada de Chroma en una lista plana de dicts.

    Chroma devuelve listas-dentro-de-listas porque permite varias queries a la
    vez. Nosotros mandamos 1 query → cogemos el índice [0] de cada campo.
    """
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    chunks: list[dict] = []
    for i, chunk_id in enumerate(ids):
        chunk = {
            "id": chunk_id,
            "text": documents[i] if i < len(documents) else "",
            "metadata": metadatas[i] if i < len(metadatas) else {},
            # Con hnsw:space=cosine, menor distance ≈ más similar
            "distance": distances[i] if i < len(distances) else None,
        }
        chunks.append(chunk)
    return chunks


def _imprimir_hits(chunks: list[dict]) -> None:
    """Muestra ranking: id, distance y fuente (útil para juzgar a ojo)."""
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.get("metadata", {}).get("source", "?")
        dist = chunk.get("distance")
        dist_txt = f"{dist:.4f}" if dist is not None else "n/a"
        print(f"[RETRIEVAL] #{i} id={chunk['id']} distance={dist_txt} source={source}")


def recuperar(pregunta: str, top_k: int | None = None) -> list[dict]:
    """Embed de la pregunta + similarity search en Chroma.

    Entrada: texto de la pregunta y cuántos chunks devolver (TOP_K por defecto).
    Salida: lista ordenada por similitud (menor distance = más parecido).

    Pasos:
      1. k = top_k if top_k is not None else TOP_K
         → Valida k >= 1; llama _log_retrieval(pregunta, k).
      2. configurar_gemini_api_key(); client = genai.Client()
         vector = embeddear_consulta(client, pregunta)
         → MISMO modelo que al indexar (si no, las distancias no tienen sentido).
      3. chroma = obtener_cliente_chroma()
         collection = obtener_coleccion(chroma, crear=False)
         → crear=False: si no hay índice, debe fallar (no crear colección vacía).
         Si collection.count() == 0 → RuntimeError pidiendo --index.
      4. results = collection.query(
             query_embeddings=[vector],
             n_results=min(k, collection.count()),  # no pedir más de los que hay
             include=["documents", "metadatas", "distances"],
         )
      5. chunks = _resultados_a_chunks(results)
         _imprimir_hits(chunks)
         return chunks
    """
    # 1) Resolver K (permite override desde --top-k o desde eval)
    k = top_k if top_k is not None else TOP_K
    if k < 1:
        raise ValueError("top_k debe ser >= 1")

    _log_retrieval(pregunta, k)

    # 2) Misma API / mismo modelo de embedding que al indexar (Sprint 8)
    configurar_gemini_api_key()
    client = genai.Client()
    vector = embed_consulta(pregunta)

    # 3) Abrir el índice ya existente (crear=False → no inventar colección vacía)
    chroma = obtener_cliente_chroma()
    collection = obtener_coleccion(chroma, crear=False)

    if collection.count() == 0:
        raise RuntimeError(
            "La colección Chroma está vacía. Ejecuta: python main.py --index"
        )

    # 4) Similarity search: el vector de la pregunta vs los vectores indexados
    results = collection.query(
        query_embeddings=[vector],
        n_results=min(k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    # 5) Normalizar formato + loguear hits para inspección humana
    chunks = _resultados_a_chunks(results)
    _imprimir_hits(chunks)
    return chunks
