"""Comprobaciones automáticas (--check) sin llamar a Gemini ni Chroma."""

import inspect
import re

from config import ENTREGABLES_DIR

_MARCADOR_TODO = re.compile(r"\bTODO\b", re.IGNORECASE)


def _tiene_marcador_todo(texto: str) -> bool:
    return bool(_MARCADOR_TODO.search(texto))


def _funcion_pendiente(modulo, nombre: str) -> bool:
    fn = getattr(modulo, nombre, None)
    if fn is None or not inspect.isfunction(fn):
        return True
    try:
        codigo = inspect.getsource(fn)
    except OSError:
        codigo = ""
    return "NotImplementedError" in codigo


def verificar_index() -> tuple[bool, list[str]]:
    errores: list[str] = []
    try:
        import index as index_mod
    except ImportError as exc:
        return False, [f"No se pudo importar index.py: {exc}"]

    for nombre in (
        "obtener_cliente_chroma",
        "obtener_coleccion",
        "ejecutar_indexacion",
    ):
        if _funcion_pendiente(index_mod, nombre):
            errores.append(f"Implementa {nombre}() en index.py")

    return len(errores) == 0, errores


def verificar_retriever() -> tuple[bool, list[str]]:
    errores: list[str] = []
    try:
        import retrieve as retriever_mod
    except ImportError as exc:
        return False, [f"No se pudo importar retriever.py: {exc}"]

    if _funcion_pendiente(retriever_mod, "recuperar"):
        errores.append("Implementa recuperar() en retriever.py")

    return len(errores) == 0, errores


def verificar_eval() -> tuple[bool, list[str]]:
    errores: list[str] = []
    try:
        import eval_retrival as eval_mod
    except ImportError as exc:
        return False, [f"No se pudo importar eval_retrieval.py: {exc}"]

    for nombre in ("evaluar_pregunta", "ejecutar_evaluacion"):
        if _funcion_pendiente(eval_mod, nombre):
            errores.append(f"Implementa {nombre}() en eval_retrieval.py")

    return len(errores) == 0, errores


def verificar_entregable() -> tuple[bool, list[str]]:
    errores: list[str] = []
    reflexion = ENTREGABLES_DIR / "reflexion_retrieval.md"

    if not reflexion.is_file():
        return False, ["Falta reflexion_retrieval.md"]

    texto = reflexion.read_text(encoding="utf-8")
    if _tiene_marcador_todo(texto):
        errores.append("Completa reflexion_retrieval.md (quedan marcadores TODO)")
    if len(texto.strip()) < 400:
        errores.append("reflexion_retrieval.md: añade más detalle (mín. ~400 caracteres)")

    return len(errores) == 0, errores
