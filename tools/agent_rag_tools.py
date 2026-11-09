"""
Etapa 02 - RAG completo + tools (LangGraph)

Instalacion:
  pip install langgraph langchain-anthropic langchain-chroma langchain-huggingface \
              langchain-text-splitters sentence-transformers requests

Estructura esperada:
  ./knowledge/   -> .txt / .md con tu base de conocimiento (incluye contexto_agente_consultor_pc.txt)
  ./uploads/     -> unico directorio desde el que se pueden leer imagenes
  ANTHROPIC_API_KEY en el entorno

Uso:
  python agent_rag_tools.py index                              # (re)indexar
  python agent_rag_tools.py test rag_ask '{"question":"Que es el cuello de botella?"}'
  python agent_rag_tools.py test convert_currency '{"amount":500,"from_cur":"EUR","to_cur":"USD"}'
  python agent_rag_tools.py test analyze_pc_image '{"image_path":"uploads/pc.jpg","question":"Que piezas ves?"}'
  python agent_rag_tools.py chat                               # agente completo en el grafo
"""

import base64
import functools
import json
import mimetypes
import os
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.prebuilt import create_react_agent

from tools import run_tool as run_complex
from tools import run_tool as run_simple

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------


KNOWLEDGE_DIR = Path("knowledge")
UPLOADS_DIR = Path("uploads").resolve()
CHROMA_DIR = "chroma_db"
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.30"))   # umbral de abstencion: AJUSTALO con tus datos
TRACE_FILE = Path("trace.jsonl")

# ALLOWLIST de tools ejecutables y de dominios externos permitidos
TOOL_ALLOWLIST = {
    "rag_ask", "convert_currency", "analyze_pc_image", "calculate_build_total",
    "check_compatibility", "estimate_power_consumption", "analyze_bottleneck",
    "compare_components", "split_budget", "recommend_ram_storage", "recommend_monitor",
    # "search_components",   # <- tu tool de busqueda por precio, cuando la envuelvas igual
}


DOMAIN_ALLOWLIST = {"api.frankfurter.app"}

llm = ChatAnthropic(model=MODEL, temperature=0)


# ---------------------------------------------------------------------------
# 1) RAG COMPLETO: indexado + retrieve + generate + abstencion
# ---------------------------------------------------------------------------

_embeddings = None
_store = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:  # modelo multilingue (espanol OK), corre en local
        _embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _embeddings


def _get_store():
    global _store
    if _store is None:
        _store = Chroma(
            collection_name="pc_knowledge",
            embedding_function=_get_embeddings(),
            persist_directory=CHROMA_DIR,
            collection_metadata={"hnsw:space": "cosine"},  # asi el score es 1 - distancia coseno
        )
    return _store


def index_documents(reset: bool = True) -> int:
    """INDEXADO: carga -> trocea -> embeddings -> guarda en Chroma."""
    global _store
    if reset and Path(CHROMA_DIR).exists():
        _store = None
        shutil.rmtree(CHROMA_DIR)
    docs = []
    for p in sorted(KNOWLEDGE_DIR.glob("**/*")):
        if p.suffix.lower() in {".txt", ".md"}:
            docs.append(Document(page_content=p.read_text(encoding="utf-8"), metadata={"source": p.name}))
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    if chunks:
        _get_store().add_documents(chunks)
    return len(chunks)


def retrieve(question: str, k: int = 4):
    """RETRIEVE: devuelve [(doc, score)] con score en 0..1 (mayor = mas parecido)."""
    return _get_store().similarity_search_with_relevance_scores(question, k=k)


RAG_PROMPT = """Eres un asesor de hardware de PC. Responde SOLO con el CONTEXTO de abajo.
Si el contexto no contiene la respuesta, responde exactamente: NO_INFO
No inventes especificaciones. Se claro y breve.

CONTEXTO:
{context}

PREGUNTA: {question}"""

ABSTAIN_MSG = "No tengo informacion suficiente en mi base de conocimiento para responder a eso con seguridad."


def rag_answer(question: str) -> str:
    """GENERATE + ABSTENCION (doble: por umbral de score y por el propio modelo)."""
    results = retrieve(question)
    good = [(d, s) for d, s in results if s >= MIN_SCORE]
    if not good:                                   # abstencion 1: nada relevante
        return ABSTAIN_MSG
    context = "\n---\n".join(d.page_content for d, _ in good)
    answer = llm.invoke(RAG_PROMPT.format(context=context, question=question)).content.strip()
    if answer.startswith("NO_INFO"):               # abstencion 2: el modelo no encuentra la respuesta
        return ABSTAIN_MSG
    sources = ", ".join(sorted({d.metadata.get("source", "?") for d, _ in good}))
    return f"{answer}\n\n(Fuentes: {sources})"


# ---------------------------------------------------------------------------
# 4) ALLOWLIST + EJECUCION SEGURA + TRAZA  (decorador que envuelve cada tool)
# ---------------------------------------------------------------------------


TRACE: list[dict] = []


def traced(fn):
    """Aplica allowlist, captura errores y registra: nombre, args, status, preview, duracion."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        name = fn.__name__
        entry = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "tool": name,
                 "args": kwargs or list(args), "status": None, "preview": None}
        t0 = time.time()
        try:
            if name not in TOOL_ALLOWLIST:
                raise PermissionError(f"Tool '{name}' no esta en la allowlist")
            out = fn(*args, **kwargs)
            entry["status"], entry["preview"] = "ok", str(out)[:200]
            return out
        except Exception as e:  # el agente recibe el error como texto, no se cae el grafo
            entry["status"], entry["preview"] = "error", f"{type(e).__name__}: {e}"[:200]
            return f"ERROR en {name}: {type(e).__name__}: {e}"
        finally:
            entry["ms"] = round((time.time() - t0) * 1000)
            TRACE.append(entry)
            with TRACE_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    return wrapper


# ---------------------------------------------------------------------------
# 2) RAG EXPUESTO COMO TOOL
# ---------------------------------------------------------------------------


@tool
@traced
def rag_ask(question: str) -> str:
    """Responde preguntas tecnicas de hardware usando la base de conocimiento interna.
    Si no hay informacion suficiente, lo dice. Usala para conceptos, guias y reglas del asesor."""
    return rag_answer(question)


# ---------------------------------------------------------------------------
# 3a) API EXTERNA: conversion de moneda (Frankfurter, gratuita y sin clave)
# ---------------------------------------------------------------------------


@tool
@traced
def convert_currency(amount: float, from_cur: str, to_cur: str) -> str:
    """Convierte un precio entre monedas (ej. EUR a USD) con el tipo de cambio actual."""
    if amount <= 0:
        raise ValueError("amount debe ser positivo")
    from_cur, to_cur = from_cur.upper().strip(), to_cur.upper().strip()
    if not (len(from_cur) == len(to_cur) == 3):
        raise ValueError("Las monedas deben ser codigos de 3 letras (EUR, USD...)")
    url = "https://api.frankfurter.app/latest"
    if urlparse(url).hostname not in DOMAIN_ALLOWLIST:
        raise PermissionError("Dominio no permitido")
    r = requests.get(url, params={"amount": amount, "from": from_cur, "to": to_cur}, timeout=10)
    r.raise_for_status()
    data = r.json()
    return f"{amount} {from_cur} = {data['rates'][to_cur]} {to_cur} (fecha: {data['date']})"


# ---------------------------------------------------------------------------
# 3b) MULTIMODAL: analizar una imagen (foto de piezas, etiqueta, captura CPU-Z...)
# ---------------------------------------------------------------------------


@tool
@traced
def analyze_pc_image(image_path: str, question: str = "Identifica los componentes y sus especificaciones visibles.") -> str:
    """Analiza una imagen (foto de un PC, etiqueta de pieza, captura de CPU-Z/HWInfo) y responde sobre ella."""
    p = Path(image_path).resolve()
    if UPLOADS_DIR not in p.parents:                       # seguridad: solo dentro de ./uploads
        raise PermissionError("Solo se pueden leer imagenes dentro de ./uploads")
    mime = mimetypes.guess_type(p.name)[0]
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        raise ValueError("Formato no soportado (usa png, jpg o webp)")
    if p.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("Imagen demasiado grande (max 5 MB)")
    b64 = base64.b64encode(p.read_bytes()).decode()
    msg = HumanMessage(content=[
        {"type": "text", "text": question + "\nSi algo no se ve claro, dilo; no inventes datos."},
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
    ])
    return llm.invoke([msg]).content


# ---------------------------------------------------------------------------
# 3c) HERRAMIENTA AUXILIAR: reutiliza tus tools anteriores via run_tool
# ---------------------------------------------------------------------------


@tool
@traced
def calculate_build_total(items: list[dict], budget: float | None = None, vat_percent: float = 0) -> dict:
    """Suma los precios de la build (items: [{name, price}]), aplica IVA y compara con el presupuesto."""
    from tools import run_tool        # el archivo que ya creamos
    return run_tool("calculate_build_total", {"items": items, "budget": budget, "vat_percent": vat_percent})
    # Mismo patron para el resto: envuelve check_compatibility, estimate_power_consumption, etc.
    # y anade sus nombres a TOOL_ALLOWLIST.
    
@tool
@traced
def check_compatibility(cpu: dict | None = None, motherboard: dict | None = None,
                        ram: dict | None = None, gpu: dict | None = None,
                        case: dict | None = None, psu: dict | None = None,
                        cooler: dict | None = None, storage: list[dict] | None = None) -> dict:
    """Verifica la compatibilidad entre componentes de una build. Usala siempre antes de dar una build final."""
    args = dict(cpu=cpu, motherboard=motherboard, ram=ram, gpu=gpu,
                case=case, psu=psu, cooler=cooler, storage=storage)
    return run_complex("check_compatibility", {k: v for k, v in args.items() if v is not None})


@tool
@traced
def estimate_power_consumption(cpu_tdp_w: float, gpu_tdp_w: float, overclock: bool = False,
                               current_psu_w: float | None = None) -> dict:
    """Estima el consumo maximo de la build y recomienda la potencia de la fuente."""
    args = {"cpu_tdp_w": cpu_tdp_w, "gpu_tdp_w": gpu_tdp_w, "overclock": overclock}
    if current_psu_w is not None:
        args["current_psu_w"] = current_psu_w
    return run_complex("estimate_power_consumption", args)


@tool
@traced
def analyze_bottleneck(cpu_score: float, gpu_score: float, resolution: str, use_case: str) -> dict:
    """Analiza el cuello de botella CPU/GPU. resolution: 1080p/1440p/4k. use_case: gaming_competitivo, gaming_aaa, edicion_video, ia, programacion, ofimatica."""
    return run_complex("analyze_bottleneck", dict(cpu_score=cpu_score, gpu_score=gpu_score,
                                                  resolution=resolution, use_case=use_case))


@tool
@traced
def compare_components(category: str, components: list[dict]) -> dict:
    """Compara 2-5 componentes de la misma categoria (precio, rendimiento, consumo, rendimiento/precio)."""
    return run_complex("compare_components", {"category": category, "components": components})


@tool
@traced
def split_budget(total_budget: float, use_case: str) -> dict:
    """Reparte el presupuesto total entre componentes segun el uso (gaming, edicion_video, programacion, ia, ofimatica, streaming)."""
    return run_simple("split_budget", {"total_budget": total_budget, "use_case": use_case})


@tool
@traced
def recommend_ram_storage(use_case: str) -> dict:
    """Recomienda RAM y almacenamiento minimo y recomendado segun el uso."""
    return run_simple("recommend_ram_storage", {"use_case": use_case})


@tool
@traced
def recommend_monitor(use_case: str, gpu_tier: str) -> dict:
    """Sugiere resolucion y refresco de monitor. gpu_tier: basica, media o alta."""
    return run_simple("recommend_monitor", {"use_case": use_case, "gpu_tier": gpu_tier})


ALL_TOOLS = [rag_ask, convert_currency, analyze_pc_image, calculate_build_total]
TOOLS = [t for t in ALL_TOOLS if t.name in TOOL_ALLOWLIST]   # al agente solo le llegan las permitidas
TOOLS_BY_NAME = {t.name: t for t in TOOLS}

SYSTEM = (
    "Eres un asesor experto en componentes de PC. Habla en espanol, claro y cercano. "
    "Para conceptos y reglas tecnicas usa rag_ask; no inventes especificaciones. "
    "Si una tool devuelve ERROR o falta informacion, dilo y pregunta al usuario. "
    "Recuerda que precios y disponibilidad cambian: deben confirmarse en tienda."
)

ALL_TOOLS = [
    rag_ask, convert_currency, analyze_pc_image, calculate_build_total,
    check_compatibility, estimate_power_consumption, analyze_bottleneck,
    compare_components, split_budget, recommend_ram_storage, recommend_monitor,
]

# ---------------------------------------------------------------------------
# GRAFO (LangGraph) y CLI
# ---------------------------------------------------------------------------


def build_agent():
    return create_react_agent(llm, TOOLS, prompt=SYSTEM)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]

    if cmd == "index":
        print(f"Indexados {index_documents()} fragmentos.")

    elif cmd == "test":
        # 5) PROBAR CADA TOOL AISLADA antes de meterla en el grafo
        name, args = sys.argv[2], json.loads(sys.argv[3] if len(sys.argv) > 3 else "{}")
        print(TOOLS_BY_NAME[name].invoke(args))
        print("\n--- traza ---")
        print(json.dumps(TRACE, indent=2, ensure_ascii=False, default=str))

    elif cmd == "chat":
        agent = build_agent()
        history = []
        while True:
            q = input("\nTu: ").strip()
            if q in {"", "salir", "exit"}:
                break
            history.append(("user", q))
            result = agent.invoke({"messages": history})
            history = result["messages"]
            print("\nAgente:", history[-1].content)


if __name__ == "__main__":
    main()
