"""Generación de respuestas con Gemini """

from config import DEFAULT_GEMINI_MODEL, DEFAULT_GENERATION_TEMPERATURE
from gemini_auto import configurar_gemini_api_key
from google import genai


def generar_respuesta(prompt: str, modelo: str | None = None, temperatura: float | None = None) -> str:
    """Envía el prompt a Gemini y devuelve el texto de la respuesta."""
    configurar_gemini_api_key()
    client = genai.Client()
    response = client.models.generate_content(
        model=modelo or DEFAULT_GEMINI_MODEL,
        contents=prompt,
        config={"temperature": temperatura or DEFAULT_GENERATION_TEMPERATURE},
    )
    return (response.text or "").strip()