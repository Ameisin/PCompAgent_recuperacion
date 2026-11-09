"""Construcción del prompt RAG """

INSTRUCCIONES_RAG = """Eres un asistente que responde preguntas sobre componentes de ordenadores correspondientes alos requisitos del cliente.

Reglas:
- Responde ÚNICAMENTE con la información del contexto proporcionado.
- Si el contexto no contiene información suficiente, indícalo explícitamente
  (no inventes magnitudes, estaciones ni datos fuera del corpus).
- Cuando cites un hecho, menciona la fuente si aparece en el contexto.
- No inventes respuestas a preguntas ajenas al dominio (p. ej. geografía general).
"""

#------------------------------------------------------------------------------------------------
# PROMPT OPTIMIZADO PARA EL LLM
#------------------------------------------------------------------------------------------------

def build_rag_prompt(contexto: str, pregunta: str) -> str:
    """Ensambla el prompt completo para el LLM."""
    return (
        f"{INSTRUCCIONES_RAG}\n\n"
        f"--- CONTEXTO RECUPERADO ---\n"
        f"{contexto.strip()}\n\n"
        f"--- PREGUNTA ---\n"
        f"{pregunta.strip()}\n\n"
        f"--- RESPUESTA ---"
    )
