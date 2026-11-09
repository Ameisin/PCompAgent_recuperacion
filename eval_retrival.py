"""Evaluación del retrieval


Esto es evaluación del RETRIEVAL (no del LLM). La reflexión escrita va en
entregables/reflexion_retrieval.md.


"""

import json
from pathlib import Path

from config import QUERIES_EVAL_JSON, TOP_K, TOP_K_CANDIDATES
from context import formatear_contexto
from retrieve import recuperar


def cargar_preguntas_eval(ruta: Path | None = None) -> list[dict]:
    """Lee el JSON con preguntas de prueba.

    Cada pregunta puede traer:
      - id, texto
      - fuente_esperada (orientativa: no es un test automático)
      - notas (pista pedagógica para el alumno)
    """
    ruta = ruta or QUERIES_EVAL_JSON
    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta}")
    data = json.loads(ruta.read_text(encoding="utf-8"))
    return data.get("preguntas", [])


def _nombre_fuente_corto(metadata: dict) -> str:
    """Solo el nombre de fichero (más legible que la ruta completa)."""
    source = metadata.get("source", "?")
    return Path(str(source)).name


def evaluar_pregunta(pregunta: str, top_k: int) -> dict:
    """Una pregunta + un K → resumen del mejor hit y preview del contexto.


    Nota: el “mejor” hit es el primero porque Chroma ya ordena por distancia.

    Pasos:
      1. chunks = recuperar(pregunta, top_k=top_k)
      2. mejor = chunks[0] si hay hits, si no {}
      3. return un dict con:
           pregunta, top_k, hits,
           mejor_id, mejor_distance, mejor_fuente,
           contexto_preview  (p. ej. formatear_contexto(chunks[:1])[:300])
    """
    # 1) Reutilizamos el retriever de la Fase 2 (misma ruta que --query)
    chunks = recuperar(pregunta, top_k=top_k)
    # 2) Chroma ya ordena por distancia → el primero es el “mejor” hit
    mejor = chunks[0] if chunks else {}
    # 3) Dict resumen + preview corto para la reflexión
    return {
        "pregunta": pregunta,
        "top_k": top_k,
        "hits": len(chunks),
        "mejor_id": mejor.get("id"),
        "mejor_distance": mejor.get("distance"),
        "mejor_fuente": _nombre_fuente_corto(mejor.get("metadata", {})),
        "contexto_preview": formatear_contexto(chunks[:1])[:300],
    }


def ejecutar_evaluacion(
    top_k_list: list[int] | None = None,
    mostrar_contexto: bool = False,
) -> list[dict]:
    """Barrido completo: todas las preguntas × varios valores de K.

    Cómo usarlo en la reflexión:
      - Compara FAQ vs CSV en q1–q4.
      - Mira si K=5 mete ruido.
      - En la pregunta fuera de corpus, las distances suelen ser peores o
        muy parecidas entre sí (señal de “no hay evidencia”).

    Pasos:
      1. preguntas = cargar_preguntas_eval()
         ks = top_k_list or TOP_K_CANDIDATES
         Imprimir cabecera (nº de preguntas y valores de K).
      2. Para cada pregunta del JSON:
           - Imprimir id, texto, notas y fuente_esperada (si existen).
             fuente_esperada es orientativa: sirve para razonar, no para assert.
           - Para cada k en ks:
               resumen = evaluar_pregunta(texto, top_k=k)
               Loguear: K=… → mejor=… distance=…
               (Opcional) si mostrar_contexto, imprimir formatear_contexto(...)
      3. return la lista de resultados (útil si más adelante guardas un informe).
    """
    # 1) Cargar set fijo de preguntas y decidir qué K probar
    preguntas = cargar_preguntas_eval()
    ks = top_k_list or TOP_K_CANDIDATES

    print("\n=== Evaluación del retrieval ===")
    print(f"Preguntas: {len(preguntas)} | Valores de K: {ks}\n")

    resultados: list[dict] = []

    # 2) Por cada pregunta: contexto pedagógico + barrido de K
    for item in preguntas:
        texto = item["texto"]
        notas = item.get("notas", "")
        fuente_esperada = item.get("fuente_esperada", "")

        print(f"\n--- {item.get('id', '?')}: {texto} ---")
        if notas:
            print(f"  Notas: {notas}")
        if fuente_esperada:
            print(f"  Fuente esperada (orientativa): {fuente_esperada}")

        for k in ks:
            resumen = evaluar_pregunta(texto, top_k=k)
            resultados.append({**item, **resumen})
            print(
                f"  K={k} → mejor={resumen['mejor_fuente']} "
                f"distance={resumen['mejor_distance']}"
            )
            if mostrar_contexto and k == (TOP_K if TOP_K in ks else ks[0]):
                print(formatear_contexto(recuperar(texto, top_k=k)))

    # 3) Devolver resultados acumulados
    print("\n=== Fin evaluación ===")
    return resultados
