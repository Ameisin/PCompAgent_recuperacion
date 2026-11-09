"""Tool multimodal: describir_imagen, de imagen a texto con Gemini (Sprint 13, notebook 5).

Solo lee imágenes de assets/ (misma idea de seguridad que la tool analyze_pc_image
del compañero, que limitaba la lectura a ./uploads).
"""

import mimetypes
from pathlib import Path

from google import genai
from google.genai import types
from langchain_core.tools import tool

from src import config_grafo
from src.llm import exigir_api_key, limitador


@tool
def describir_imagen(
    pregunta: str = "Describe los componentes y especificaciones que aparecen.",
    ruta: str = "",
) -> str:
    """Lee una imagen (por defecto assets/imagen_demo.jpg: ficha técnica de una pieza de PC)
    y responde a la pregunta sobre lo que se ve. Úsala cuando el usuario hable de una
    imagen, foto, captura, etiqueta o ficha.
    """
    p = Path(ruta).resolve() if ruta else config_grafo.IMAGEN_DEMO_PATH
    if config_grafo.ASSETS_DIR.resolve() not in p.parents:
        return "Error: solo se pueden leer imágenes de la carpeta assets/."
    mime = mimetypes.guess_type(p.name)[0]
    if mime not in {"image/png", "image/jpeg", "image/webp"} or not p.is_file():
        return f"Error: no hay una imagen png/jpg/webp en {p.name}."
    if p.stat().st_size > config_grafo.IMAGEN_MAX_BYTES:
        return "Error: imagen demasiado grande (máx. 5 MB)."

    exigir_api_key()
    limitador(config_grafo.GEMINI_MODEL, config_grafo.LLM_RPM).acquire()
    cliente = genai.Client()  # en variable: un Client temporal se cierra antes de que acabe la petición
    respuesta = cliente.models.generate_content(
        model=config_grafo.GEMINI_MODEL,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=p.read_bytes(), mime_type=mime),
                    types.Part.from_text(text=f"{pregunta}\nSi algo no se lee bien, dilo; no inventes datos."),
                ],
            )
        ],
    )
    return (respuesta.text or "").strip() or "(la imagen no devolvió texto)"
