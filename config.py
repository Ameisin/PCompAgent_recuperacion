"""
Configuración centralizada del proyecto:
cambiar un parámetro = editar un solo archivo.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  ## lee .env si existe (nunca se sube al repo)

## ---------------------------------------------------------------------------
## Rutas
## ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CSV_DIR = DATA_DIR / "csv"          ## componentes + videojuegos (formato 1: CSV)
DOCS_DIR = DATA_DIR / "md"        ## guías en Markdown/TXT/PDF (formato 2: texto)
QUERIES_DIR = BASE_DIR / "queries"

OUTPUT_DIR = BASE_DIR / "output"    ## artefactos generados (gitignored)
CHUNKS_JSON = OUTPUT_DIR / "chunks.json"
EMBEDDINGS_JSON = OUTPUT_DIR / "embeddings.json"
LOGS_DIR = OUTPUT_DIR / "logs"
LOG_FILE = LOGS_DIR / "rag.log"                 ## log legible (consola + fichero)
CONSULTAS_JSONL = LOGS_DIR / "consultas.jsonl"  ## una línea JSON por consulta (lo lee Streamlit)
EVAL_RETRIEVAL_JSON = OUTPUT_DIR / "eval_retrieval.json"

CHROMA_DIR = BASE_DIR / "chroma"    ## índice persistente (gitignored)
COLLECTION_NAME = "pc_gaming"

## ---------------------------------------------------------------------------
## Corpus: qué CSV se cargan y con qué categoría
## ---------------------------------------------------------------------------
## nombre de fichero -> (slug de categoría para metadatos/filtros, nombre en español)
CATEGORIAS_CSV = {
    "cpu.csv": ("cpu", "Procesador"),
    "video-card.csv": ("gpu", "Tarjeta gráfica"),
    "motherboard.csv": ("placa_base", "Placa base"),
    "memory.csv": ("ram", "Memoria RAM"),
    "internal-hard-drive.csv": ("almacenamiento", "Almacenamiento"),
    "power-supply.csv": ("fuente", "Fuente de alimentación"),
    "case.csv": ("caja", "Caja / chasis"),
    "cpu-cooler.csv": ("disipador", "Refrigeración de CPU"),
    "case-fan.csv": ("ventilador", "Ventilador de caja"),
    "thermal-paste.csv": ("pasta_termica", "Pasta térmica"),
    "sound-card.csv": ("tarjeta_sonido", "Tarjeta de sonido"),
    "wireless-network-card.csv": ("tarjeta_red", "Tarjeta de red inalámbrica"),
    ## Excluidos por alcance (periféricos / sin datos útiles): webcam.csv, caseaccessory.csv
}
CSV_VIDEOJUEGOS = "videogame_requirements.csv"

## Filtrado de filas (documentado en README e informe):
##  - SOLO_CON_PRECIO: los productos sin precio no sirven para recomendar por presupuesto.
##  - MAX_FILAS_POR_CSV: tope por categoría para mantener el índice manejable y regenerable.
##    None = sin tope. Los CSV vienen ordenados por popularidad (PCPartPicker), así que
##    quedarse con las primeras N filas conserva los productos más relevantes.
SOLO_CON_PRECIO = True
MAX_FILAS_POR_CSV = int(os.getenv("MAX_FILAS_POR_CSV", "400"))
MAX_FILAS_VIDEOJUEGOS = int(os.getenv("MAX_FILAS_VIDEOJUEGOS", "2500"))
ANIO_MIN_VIDEOJUEGOS = 2019  ## juegos anteriores tienen requisitos poco relevantes hoy (~2.300 juegos desde 2019)

## Límite global de chunks a indexar (None = todos). Útil para pruebas rápidas
## (p. ej. MAX_CHUNKS=50) sin gastar cuota de API. Si lo cambias, regenera el índice.
_max_chunks = os.getenv("MAX_CHUNKS", "")
MAX_CHUNKS = int(_max_chunks) if _max_chunks.strip() else None

## ---------------------------------------------------------------------------
## Chunking (solo aplica a documentos de texto; cada fila de CSV ya es un chunk)
## ---------------------------------------------------------------------------
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
TIPOS_DOC_FRAGMENTABLES = {"guia"}  ## tipo de Document que pasa por el splitter
## "recursive"        -> RecursiveCharacterTextSplitter directo (como en la live review)
## "markdown_headers" -> primero MarkdownHeaderTextSplitter por secciones (#, ##, ###) y después
##                      recursive; cada chunk lleva su ruta de sección como contexto. (A/B en el informe)
ESTRATEGIA_CHUNKING = os.getenv("ESTRATEGIA_CHUNKING", "markdown_headers")

## ---------------------------------------------------------------------------
## Embeddings
## ---------------------------------------------------------------------------
## "gemini" (camino principal del bootcamp, requiere GEMINI_API_KEY)
## "huggingface" (sentence-transformers en local, sin API key)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()
DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"
DEFAULT_GENERATION_TEMPERATURE = 0.3
DEFAULT_GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
DEFAULT_GEMINI_EMBEDDING_DIM = 768        ## gemini-embedding-001 admite 768/1536/3072 (MRL)
HF_EMBEDDING_MODEL = os.getenv(
    "HF_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

EMBED_BATCH_SIZE = 100            ## textos por llamada (límite de la API de Gemini: 100)
EMBED_MAX_REINTENTOS = 5          ## ante 429 / errores transitorios
EMBED_ESPERA_BASE_S = 2.0         ## backoff exponencial: 2, 4, 8, 16, 32 s


def nombre_modelo_embedding() -> str:
    """Identificador del modelo activo (se guarda en la colección Chroma)."""
    if EMBEDDING_PROVIDER == "gemini":
        return f"gemini:{DEFAULT_GEMINI_EMBEDDING_MODEL}:{DEFAULT_GEMINI_EMBEDDING_DIM}"
    if EMBEDDING_PROVIDER == "huggingface":
        return f"huggingface:{HF_EMBEDDING_MODEL}"
    raise ValueError(f"EMBEDDING_PROVIDER no soportado: {EMBEDDING_PROVIDER!r}")


## ---------------------------------------------------------------------------
## Retrieval
## ---------------------------------------------------------------------------
TOP_K = 5                  ## chunks que se recuperan por defecto
TOP_K_MAX = 20 
TOP_K_CANDIDATES = [1, 3, 5]
## tope de seguridad para --k
LONGITUD_MAX_PREGUNTA = 500  ## caracteres; más largo -> se rechaza sin llamar a la API
K_EVALUACION = [1, 3, 5]   ## barrido de K en la evaluación de retrieval

## Palabras clave -> categoría, para filtrar por metadatos cuando la pregunta lo deja claro.
## (Se usa en retrieve.detectar_categoria; el usuario puede forzarla con --categoria.)
PALABRAS_CLAVE_CATEGORIA = {
    "cpu": ["procesador", "cpu", "ryzen", "core i", "intel core", "núcleos", "nucleos"],
    "gpu": ["gráfica", "grafica", "gpu", "tarjeta de video", "geforce", "rtx", "radeon", "rx "],
    "placa_base": ["placa base", "placa madre", "motherboard", "socket", "chipset", "am5", "am4", "lga"],
    "ram": ["memoria ram", " ram", "ddr4", "ddr5", "módulos", "modulos"],
    "almacenamiento": ["ssd", "nvme", "disco duro", "hdd", "almacenamiento", "m.2"],
    "fuente": ["fuente de alimentación", "fuente de alimentacion", "psu", "vatios", "watios", " w ", "80 plus", "modular"],
    "caja": ["caja", "chasis", "torre", "gabinete"],
    "disipador": ["disipador", "refrigeración", "refrigeracion", "cooler", "aio", "líquida", "liquida"],
    "ventilador": ["ventilador", "ventiladores", "airflow"],
    "pasta_termica": ["pasta térmica", "pasta termica"],
    "tarjeta_sonido": ["tarjeta de sonido", "sound blaster"],
    "tarjeta_red": ["wifi", "wi-fi", "tarjeta de red", "inalámbrica", "inalambrica"],
    "videojuego": ["juego", "videojuego", "requisitos", "jugar", "fps"],
}

## ---------------------------------------------------------------------------
## EVALUACION
## ---------------------------------------------------------------------------

QUERIES_EVAL_JSON = Path(__file__).parent / "queries" / "preguntas_eval.json"

## ---------------------------------------------------------------------------
## VERIFICACION
## ---------------------------------------------------------------------------

ENTREGABLES_DIR = Path(__file__).parent / "entregables"


def ruta_corta(ruta: Path) -> str: ## Ruta relativa al proyecto para logs ('output/chunks.json'); absoluta si está fuera.
    try:
        return Path(ruta).resolve().relative_to(BASE_DIR).as_posix()
    except ValueError:
        return str(ruta)
