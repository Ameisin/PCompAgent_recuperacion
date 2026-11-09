"""Reglas deterministas en Python que acompañan al grafo (no llaman al LLM).

Idea de clase: "el modelo propone, Python decide". Aquí viven tres reglas
propias del dominio PC que el grafo usa para no depender del LLM en lo crítico:

  1. extraer_preferencias: presupuesto, usos y categorías del pedido.
  2. calcular_faltan_datos: si falta lo mínimo para recomendar, se pregunta
     al usuario en lugar de inventar una configuración genérica.
  3. resumen_presupuesto: suma los precios del plan y comprueba el presupuesto
     ANTES de la pausa HITL, para que la persona apruebe con el dato real.
"""

import re

import config as config_rag  # PALABRAS_CLAVE_CATEGORIA del RAG (PB1)

# Uso principal del equipo -> palabras que lo delatan en el pedido.
USOS = {
    "gaming": ["gaming", "gamer", "jugar", "juego", "videojuego", "fps", "1080p", "1440p", "2160p"],
    "trabajo": ["oficina", "ofimática", "ofimatica", "excel", "word", "navegador", "videollamada",
                "teletrabajo", "trabajo", "estudiar", "estudios"],
    "edicion": ["edición", "edicion", "editar", "render", "renderizar", "diseño", "diseno",
                "photoshop", "premiere", "davinci", "blender", "streaming"],
}

# Palabras que indican que se pide un equipo completo (no una pieza suelta).
PALABRAS_PC_COMPLETO = ["pc", "ordenador", "equipo", "torre", "configuración", "configuracion",
                        "build", "montar", "armar", "montaje"]

# Número con separador de miles opcional: 700 | 1200 | 1.200 | 1,200 | 451.50
_NUMERO = r"(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)"
_MONEDA = r"(\$|€|usd|eur|euros?|d[oó]lares?)"

_PATRONES_PRESUPUESTO = [
    re.compile(rf"(?:\$|€)\s*{_NUMERO}", re.IGNORECASE),                       # $700
    re.compile(rf"{_NUMERO}\s*{_MONEDA}", re.IGNORECASE),                      # 700 € / 700 dólares
    re.compile(rf"presupuesto\s+(?:\w+\s+){{0,2}}?(?:de\s+)?{_NUMERO}", re.IGNORECASE),  # presupuesto de 700
]

_PATRON_PRECIO = re.compile(
    rf"(?:\$|€)\s*{_NUMERO}|{_NUMERO}\s*(?:\$|€|usd|eur)", re.IGNORECASE
)


def _a_numero(texto: str) -> float | None:
    """'1.200' -> 1200.0 · '1,299.99' -> 1299.99 · '451.50' -> 451.5 · '451,50' -> 451.5."""
    t = texto.strip()
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", t):
        t = re.sub(r"[.,]", "", t)                 # solo separadores de miles
    elif re.fullmatch(r"\d{1,3}(?:,\d{3})+\.\d{1,2}", t):
        t = t.replace(",", "")                     # formato US: 1,299.99
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+,\d{1,2}", t):
        t = t.replace(".", "").replace(",", ".")   # formato ES: 1.299,99
    else:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _contiene(texto: str, palabras: list[str]) -> bool:
    """Búsqueda por palabra (con espacios de relleno, como en config.PALABRAS_CLAVE_CATEGORIA)."""
    t = f" {texto.lower()} "
    return any(re.search(rf"(?<!\w){re.escape(p.strip())}(?!\w)", t) for p in palabras)


def _detectar_presupuesto(texto: str) -> float | None:
    for patron in _PATRONES_PRESUPUESTO:
        m = patron.search(texto)
        if m:
            valor = _a_numero(m.group(1))
            if valor and valor > 0:
                return valor
    return None


def extraer_preferencias(textos: list[str]) -> dict:
    """Preferencias del usuario a partir de TODOS sus mensajes del hilo (en orden).

    Se mira el historial completo (no solo el último mensaje) para que una
    respuesta del tipo "unos 800 dólares" complete un pedido anterior. Si el
    presupuesto aparece varias veces, manda el MÁS RECIENTE ("mejor 550 USD").
    """
    texto = " \n".join(t for t in textos if t)
    presupuesto = next(
        (p for p in (_detectar_presupuesto(t) for t in reversed(textos) if t) if p),
        None,
    )
    usos = [uso for uso, palabras in USOS.items() if _contiene(texto, palabras)]
    categorias = [
        cat
        for cat, palabras in config_rag.PALABRAS_CLAVE_CATEGORIA.items()
        if cat != "videojuego" and _contiene(texto, palabras)
    ]
    return {
        "presupuesto": presupuesto,
        "usos": usos,
        "categorias": categorias,
        "pc_completo": _contiene(texto, PALABRAS_PC_COMPLETO) or not categorias,
    }


def calcular_faltan_datos(preferencias: dict) -> list[str]:
    """Qué falta para poder recomendar sin inventar.

    - Pieza suelta ("¿qué SSD para edición 4K?"): basta con la categoría.
    - Equipo completo: hacen falta presupuesto y uso.
    """
    if preferencias.get("categorias") and not preferencias.get("pc_completo"):
        return []
    faltan = []
    if not preferencias.get("presupuesto"):
        faltan.append("presupuesto")
    if not preferencias.get("usos"):
        faltan.append("uso")
    return faltan


def pregunta_aclaratoria(faltan: list[str]) -> str:
    """Mensaje determinista al usuario cuando faltan datos (no gasta llamada al LLM)."""
    piezas = {
        "presupuesto": "tu **presupuesto** aproximado (p. ej. 700 USD)",
        "uso": "el **uso principal** (gaming, trabajo de oficina, edición de vídeo…)",
    }
    detalle = " y ".join(piezas[f] for f in faltan if f in piezas)
    # Se presenta el alcance del asistente: así también sirve de respuesta
    # honesta a pedidos fuera de dominio ("¿capital de Francia?").
    return (
        "Te ayudo a elegir componentes y configuraciones de PC con el catálogo del proyecto. "
        f"Para recomendarte una configuración necesito {detalle}. "
        "Si es para juegos, dime también la resolución o algún juego concreto."
    )


def resumen_presupuesto(plan: list[str], presupuesto: float | None, n_usos: int = 1) -> dict:
    """Suma el primer precio de cada viñeta del plan y lo compara con el presupuesto.

    `dentro` es None cuando no se puede decidir (sin presupuesto, sin precios o
    plan comparativo de varias configuraciones, donde la suma no tiene sentido).
    """
    total = 0.0
    con_precio = 0
    for item in plan or []:
        if re.match(r"\s*\**\s*total", item, re.IGNORECASE):
            continue  # la línea de total no se suma dos veces
        m = _PATRON_PRECIO.search(item)
        if not m:
            continue
        valor = _a_numero(m.group(1) or m.group(2))
        if valor:
            total += valor
            con_precio += 1
    total = round(total, 2)
    comparable = bool(presupuesto) and con_precio > 0 and n_usos <= 1
    return {
        "total": total if con_precio else None,
        "presupuesto": presupuesto,
        "items_con_precio": con_precio,
        "dentro": (total <= presupuesto) if comparable else None,
    }
