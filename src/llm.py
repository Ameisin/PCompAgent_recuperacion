"""LLM LangChain (Gemini) para los nodos del grafo multiagente."""

import os

from dotenv import load_dotenv
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_google_genai import ChatGoogleGenerativeAI

from gemini_auto import configurar_gemini_api_key  # carga de la API key del PB1
from src import config_grafo

# Un limitador por MODELO (la cuota gratuita es por modelo), compartido por todo
# el proceso: los nodos y la tool RAG que gastan del mismo modelo esperan su
# turno en vez de provocar un 429 de la API gratuita.
_LIMITADORES: dict[str, InMemoryRateLimiter] = {}


def limitador(modelo: str, rpm: float) -> InMemoryRateLimiter:
    """Devuelve (o crea) el limitador de `rpm` peticiones por minuto del `modelo`.

    El primero que lo crea fija el ritmo; los demás lo comparten.
    """
    nombre = modelo
    if nombre not in _LIMITADORES:
        _LIMITADORES[nombre] = InMemoryRateLimiter(
            requests_per_second=max(rpm, 0.1) / 60,
            check_every_n_seconds=0.2,
            max_bucket_size=1,  # sin ráfagas: peticiones espaciadas
        )
    return _LIMITADORES[nombre]


def exigir_api_key() -> None:
    """Carga .env y falla con un error claro si no hay GEMINI_API_KEY.

    gemini_auto.configurar_gemini_api_key() la pide con getpass si falta: en
    Streamlit o en segundo plano eso deja el proceso colgado esperando teclado.
    """
    load_dotenv()
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("Falta GEMINI_API_KEY: copia .env.example como .env y pon tu clave.")
    configurar_gemini_api_key()


def get_llm(temperature: float | None = None) -> ChatGoogleGenerativeAI:
    """Factory del chat model: misma clave (.env) que usa el RAG."""
    exigir_api_key()
    return ChatGoogleGenerativeAI(
        model=config_grafo.GEMINI_MODEL,
        google_api_key=os.environ["GEMINI_API_KEY"],
        temperature=config_grafo.TEMPERATURE if temperature is None else temperature,
        max_retries=config_grafo.LLM_REINTENTOS,  # backoff ante 429 (cuota gratuita)
        rate_limiter=limitador(config_grafo.GEMINI_MODEL, config_grafo.LLM_RPM),
    )
