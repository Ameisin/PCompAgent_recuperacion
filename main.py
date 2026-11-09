"""CLI del RAG: separa el pipeline offline (prepare / index) del online (query / ask).

Uso:
  python main.py                            # sin argumentos: prepara + indexa si hace falta y abre Streamlit
  python main.py --prepare                  # load -> clean -> chunk -> embed -> output/embeddings.json
  python main.py --index [--recreate-index] # embeddings.json -> ChromaDB
  python main.py --query "pregunta" [--top-k 3]   # solo retrieval + contexto
  python main.py --ask "pregunta" [--top-k 3]     # RAG completo (retrieval + LLM)
  python main.py --eval                     # barrido de K sobre queries/preguntas_eval.json
"""

import argparse
import sys

import chunk as ck
import clean as cln
import embed as emb
import index as ind
import load as ld
from config import TOP_K


# ---------------------------------------------------------------------------
# Pipeline offline
# ---------------------------------------------------------------------------
def cmd_prepare() -> None:
    print("Cargando documentos del corpus…")
    documentos = ld.cargar_documentos()
    print(f"Documentos cargados: {len(documentos)}")

    print("Limpiando documentos…")
    documentos = cln.limpiar_documentos(documentos)
    print(f"Documentos tras limpieza: {len(documentos)}")

    print("Fragmentando en chunks…")
    chunks = ck.fragmentar_documentos(documentos)
    print(f"Chunks generados: {len(chunks)}")

    print("Buscando embeddings en caché…")
    vectores = emb.cargar_embeddings_cache(chunks)
    if vectores is None:
        print("Generando embeddings (llama a la API)…")
        vectores = emb.embed_documentos([c.page_content for c in chunks])
    else:
        print("Caché válida, no se llama a la API.")

    emb.guardar_embeddings_json(chunks, vectores)
    print(f"Embeddings guardados: {len(vectores)}")


def cmd_index(recreate: bool) -> None:
    total = ind.ejecutar_indexacion(recreate=recreate)
    print(f"Indexación completada. Documentos en la colección: {total}")


def _indice_listo() -> bool:
    """True si la colección Chroma existe y tiene documentos."""
    from chromadb.errors import NotFoundError

    try:
        coleccion = ind.obtener_coleccion(ind.obtener_cliente_chroma(), crear=False)
    except NotFoundError:
        return False
    return coleccion.count() > 0


# ---------------------------------------------------------------------------
# Pipeline online
# ---------------------------------------------------------------------------
def cmd_query(pregunta: str, top_k: int) -> None:
    from context import imprimir_contexto
    from retrieve import recuperar

    chunks = recuperar(pregunta, top_k=top_k)
    imprimir_contexto(chunks)


def cmd_ask(pregunta: str, top_k: int) -> None:
    from logic import responder

    resultado = responder(pregunta, top_k=top_k)
    if resultado["error"]:
        print(f"Error: {resultado['error']}")
        return
    print("\n--- Respuesta ---")
    print(resultado["respuesta"])
    print("\n--- Fuentes ---")
    for fuente in resultado["fuentes"]:
        print(f"- {fuente}")
    print(f"\n[chunks={len(resultado['chunks'])} tiempo={resultado['tiempo_ms']} ms]")


def cmd_eval() -> None:
    from eval_retrival import ejecutar_evaluacion

    ejecutar_evaluacion()


def cmd_app(recreate: bool) -> None:
    """Flujo completo: prepara e indexa si hace falta y abre Streamlit."""
    if recreate or not _indice_listo():
        cmd_prepare()
        cmd_index(recreate=recreate)
    else:
        print("Índice ya construido, se omite la indexación (usa --recreate-index para regenerarlo).")

    from streamlit.web import cli as stcli

    print("Abriendo la interfaz Streamlit…")
    sys.argv = ["streamlit", "run", "app.py"]
    sys.exit(stcli.main())


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="RAG de componentes de PC. Sin argumentos: indexa si hace falta y abre Streamlit."
    )
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--prepare", action="store_true", help="Cargar, limpiar, fragmentar y vectorizar el corpus")
    grupo.add_argument("--index", action="store_true", help="Indexar embeddings.json en ChromaDB")
    grupo.add_argument("--query", metavar="PREGUNTA", help="Solo retrieval: muestra los chunks recuperados")
    grupo.add_argument("--ask", metavar="PREGUNTA", help="RAG completo: retrieval + respuesta del LLM")
    grupo.add_argument("--eval", action="store_true", help="Evaluación de retrieval con varios K")

    parser.add_argument("--recreate-index", action="store_true", help="Borra la colección antes de indexar")
    parser.add_argument("--top-k", type=int, default=TOP_K, help=f"Chunks a recuperar (por defecto {TOP_K})")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.prepare:
            cmd_prepare()
        elif args.index:
            cmd_index(recreate=args.recreate_index)
        elif args.query:
            cmd_query(args.query, args.top_k)
        elif args.ask:
            cmd_ask(args.ask, args.top_k)
        elif args.eval:
            cmd_eval()
        else:
            cmd_app(recreate=args.recreate_index)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())