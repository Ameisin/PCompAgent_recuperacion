"""Configura GEMINI_API_KEY antes de llamar a la API (dado)."""

import getpass
import os

from dotenv import load_dotenv

_configured = False


def configurar_gemini_api_key() -> None:
    """Carga la API key una sola vez por ejecución."""
    global _configured
    if _configured:
        return

    load_dotenv()

    if not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = getpass.getpass(
            "Pega aquí tu GEMINI_API_KEY (input oculto): "
        )

    print(
        "GEMINI_API_KEY configurada:",
        "sí" if os.getenv("GEMINI_API_KEY") else "no",
    )
    _configured = True
