"""Configuración del grafo multiagente: modelo, límites y demo.

Reutiliza config.py (PB1) para no duplicar el modelo de Gemini ni los límites
del RAG. Todo lo que es exclusivo del agente vive aquí: cambiar un límite =
editar un solo archivo (misma idea que config.py del RAG).
"""

import os

import config as config_rag  # config.py del PB1 (raíz del proyecto)

## ---------------------------------------------------------------------------
## Modelo (LangChain ChatGoogleGenerativeAI)
## ---------------------------------------------------------------------------
## En la capa gratuita la cuota es POR MODELO. El RAG (PB1) genera con
## config_rag.DEFAULT_GEMINI_MODEL; el agente usa por defecto otro modelo para no
## competir por la misma cuota (5 peticiones/min en gemini-3-flash). Se puede
## cambiar sin tocar código: AGENTE_GEMINI_MODEL=gemini-3-flash-preview
GEMINI_MODEL = os.getenv("AGENTE_GEMINI_MODEL", "gemini-3.1-flash-lite")
TEMPERATURE = 0.3              ## especialistas y sintetizar
TEMPERATURE_SUPERVISOR = 0.0   ## el supervisor solo enruta: cuanto más determinista, mejor
LLM_REINTENTOS = 3             ## reintentos ante 429 / errores transitorios (API gratuita)

## Modelo con el que GENERA la tool RAG (responder(..., modelo=...)); el retrieval
## sigue igual. El del PB1 (gemini-3-flash) tiene en la capa gratuita 5 peticiones/min
## y 20/día: con ~7 consultas por turno, el agente se quedaría sin cuota en 3 turnos.
## Por eso, por defecto, usa el modelo del agente. Para el modelo del PB1:
## AGENTE_RAG_MODEL=gemini-3-flash-preview
RAG_GEMINI_MODEL = os.getenv("AGENTE_RAG_MODEL", GEMINI_MODEL)

## Ritmo máximo de llamadas (peticiones por minuto) para no chocar con el 429.
## Hay un limitador por MODELO: si agente y RAG usan el mismo, comparten ritmo.
## Ajusta a la cuota de tu clave: https://ai.dev/rate-limit
LLM_RPM = float(os.getenv("AGENTE_LLM_RPM", "10"))  ## modelo del agente
RAG_RPM = float(os.getenv("AGENTE_RAG_RPM", "4"))   ## solo si el RAG usa OTRO modelo (gemini-3-flash: 5/min; margen)
RAG_ESPERA_MAX_429_S = 60  ## si aun así llega un 429, se espera lo que pide el servidor (con tope) y se reintenta 1 vez

## ---------------------------------------------------------------------------
## Límites decididos en Python (no por el LLM)
## ---------------------------------------------------------------------------
MAX_STEPS_DEFAULT = 4   ## vueltas modelo ↔ tools DENTRO de un especialista (CPU → socket → placa → RAM)
MAX_TURNS_DEFAULT = 6   ## mensajes de usuario por conversación (clientes)
MAX_ITER = 8            ## vueltas del supervisor por turno (evita bucles de roles)
LONGITUD_MAX_MENSAJE = config_rag.LONGITUD_MAX_PREGUNTA  ## mismo tope que el RAG

## Supervisor con LLM (como en clase) o solo con reglas Python.
## Con la API gratuita, "0" ahorra una llamada por iteración del supervisor.
SUPERVISOR_USA_LLM = os.getenv("AGENTE_SUPERVISOR_LLM", "1").strip() != "0"

## Cuántas entradas del historial del hilo se pasan a los especialistas.
MAX_HISTORIAL_PROMPT = 6

## ---------------------------------------------------------------------------
## Tools (src/tools/)
## ---------------------------------------------------------------------------
DIVISAS_URL = "https://api.frankfurter.dev/v1/latest"   ## API pública sin clave (BCE)
DIVISAS_FALLBACK_PATH = config_rag.DATA_DIR / "divisas_fallback.json"
HTTP_TIMEOUT_SECONDS = 10
ASSETS_DIR = config_rag.BASE_DIR / "assets"             ## única carpeta de la que se leen imágenes
IMAGEN_DEMO_PATH = ASSETS_DIR / "imagen_demo.jpg"
IMAGEN_MAX_BYTES = 5 * 1024 * 1024

## ---------------------------------------------------------------------------
## Demo CLI
## ---------------------------------------------------------------------------
DEMO_MENSAJES = [
    "Quiero un PC gaming para jugar a 1080p con 60 fps estables, presupuesto de $700.",
]
