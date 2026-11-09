"""Allowlist de tools LangChain (@tool) del agente.

Solo las tools de esta lista se pueden ejecutar; si el modelo pide otra,
ejecutar_tool la bloquea. Antes de ejecutar, validar_args sanea los parámetros.

| Categoría PB2  | Tool                                        |
|----------------|---------------------------------------------|
| RAG completo   | RAG_consultar_catalogo (responder() del PB1) |
| Catálogo (CSV) | buscar_componentes                          |
| API externa    | convertir_divisa (Frankfurter + fallback)   |
| Auxiliares     | calcular_total_build, hora_actual           |
| Multimodal     | describir_imagen (Gemini, assets/)          |
"""

import re

import config as config_rag
from src.tools.auxiliares import calcular_total_build, hora_actual
from src.tools.catalogo import buscar_componentes
from src.tools.describir_imagen import describir_imagen
from src.tools.divisas import convertir_divisa
from src.tools.rag_catalogo import RAG_consultar_catalogo

TOOLS = [
    RAG_consultar_catalogo,
    buscar_componentes,
    convertir_divisa,
    calcular_total_build,
    hora_actual,
    describir_imagen,
]

TOOL_BY_NAME = {t.name: t for t in TOOLS}


def _numero(valor, por_defecto: float | None = None) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return por_defecto


def validar_args(nombre: str, args: dict | None = None) -> dict:
    """Guardrails antes de ejecutar (tipos, límites y vacíos). Lanza ValueError si no valen."""
    args = args or {}
    if nombre == "hora_actual":
        return {}
    if nombre == "RAG_consultar_catalogo":
        consulta = str(args.get("consulta") or "").strip()[: config_rag.LONGITUD_MAX_PREGUNTA]
        if not consulta:
            raise ValueError("la consulta al RAG no puede estar vacía")
        top_k = int(_numero(args.get("top_k"), config_rag.TOP_K))
        return {"consulta": consulta, "top_k": max(1, min(top_k, 10))}
    if nombre == "buscar_componentes":
        precio_max = _numero(args.get("precio_max"))
        return {
            "componente": str(args.get("componente") or "").strip().lower(),
            "precio_min": max(0.0, _numero(args.get("precio_min"), 0.0)),
            "precio_max": precio_max if precio_max and precio_max > 0 else None,
        }
    if nombre == "convertir_divisa":
        cantidad = _numero(args.get("cantidad"))
        origen = str(args.get("origen") or "").strip().upper()
        destino = str(args.get("destino") or "").strip().upper()
        if not cantidad or cantidad <= 0:
            raise ValueError("la cantidad debe ser un número positivo")
        if not (re.fullmatch(r"[A-Z]{3}", origen) and re.fullmatch(r"[A-Z]{3}", destino)):
            raise ValueError("las monedas deben ser códigos de 3 letras (EUR, USD…)")
        return {"cantidad": cantidad, "origen": origen, "destino": destino}
    if nombre == "calcular_total_build":
        precios = [p for p in (_numero(x) for x in args.get("precios") or []) if p is not None and p >= 0]
        if not precios:
            raise ValueError("hace falta al menos un precio válido")
        return {"precios": precios, "presupuesto": _numero(args.get("presupuesto"))}
    if nombre == "describir_imagen":
        limpios = {"ruta": str(args.get("ruta") or "").strip()}
        if args.get("pregunta"):
            limpios["pregunta"] = str(args["pregunta"]).strip()[:500]
        return limpios
    return args


def ejecutar_tool(nombre: str, args: dict | None = None) -> str:
    """Ejecuta una tool de la allowlist; si no está, la bloquea."""
    tool_fn = TOOL_BY_NAME.get(nombre)
    if tool_fn is None:
        return f"Error: tool '{nombre}' no está permitida."
    try:
        return str(tool_fn.invoke(validar_args(nombre, args)))
    except Exception as e:  # noqa: BLE001
        return f"Error al ejecutar {nombre}: {e}"
