"""
Convierte páginas HTML guardadas en local (p. ej. con "Guardar como..." del navegador) a
Markdown en data/docs/, listas para el pipeline de ingesta.

Uso interactivo (sin argumentos): pregunta por terminal la ruta del HTML, la URL de origen
y dónde guardar el .md:
    python scripts/convertir_html_a_markdown.py

Uso por argumentos (para automatizar o convertir varios ficheros):
    python scripts/convertir_html_a_markdown.py data/raw/gaming-cpu.html
    python scripts/convertir_html_a_markdown.py data/raw/*.html
    python scripts/convertir_html_a_markdown.py data/raw/gaming-cpu.html --url https://www.intel.la/... --salida data/docs/intel_gaming_cpu.md

Sin --salida, el .md se llama data/docs/intel_<nombre-del-html>.md. Con --url se anota la URL
de origen en la cabecera del .md (para la tabla de fuentes del README).

Este módulo contiene la función `html_a_markdown`, que también usa scripts/descargar_guia_intel.py.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "docs"
MIN_SECCIONES = 3


def html_a_markdown(html: str) -> str:
    """Extrae títulos (h1-h4), párrafos y listas del <main> y los devuelve como Markdown."""
    soup = BeautifulSoup(html, "html.parser")
    for etiqueta in soup(["script", "style", "nav", "header", "footer", "noscript", "iframe", "svg"]):
        etiqueta.decompose()

    cuerpo = soup.find("main") or soup.body or soup
    lineas: list[str] = []
    for el in cuerpo.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        texto = " ".join(el.get_text(" ", strip=True).split())
        if not texto or len(texto) < 3:
            continue
        if el.name == "h1":
            lineas.append(f"# {texto}\n")
        elif el.name == "h2":
            lineas.append(f"\n## {texto}\n")
        elif el.name in {"h3", "h4"}:
            lineas.append(f"\n### {texto}\n")
        elif el.name == "li":
            lineas.append(f"- {texto}")
        else:
            lineas.append(f"{texto}\n")

    md = "\n".join(lineas)
    md = re.sub(r"\n{3,}", "\n\n", md)
    # quitar avisos legales / cookies típicos al final
    md = re.split(r"\n#+ .*(Aviso|Cookies|Política de privacidad)", md, maxsplit=1)[0]
    return md.strip() + "\n"


def cabecera_fuente(origen: str, modo: str) -> str:
    return (
        f"Fuente: Intel, página original en {origen}\n"
        f"Fecha de descarga: {date.today().strftime('%d/%m/%Y')} ({modo}). Uso educativo (Project Break RAG).\n"
        "Texto extraído automáticamente con scripts/convertir_html_a_markdown.py.\n\n"
    )


def convertir_fichero(entrada: Path, salida: Path, url: str | None = None) -> bool:
    html = entrada.read_text(encoding="utf-8", errors="ignore")
    md = html_a_markdown(html)
    n_secciones = md.count("\n## ")
    if n_secciones < MIN_SECCIONES:
        print(f"  {entrada.name}: solo {n_secciones} secciones detectadas; revisa el HTML. No se escribe {salida.name}.")
        return False
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(cabecera_fuente(url or entrada.name, "guardada manualmente desde el navegador") + md, encoding="utf-8")
    print(f"  {entrada.name} -> {salida} ({len(md)} caracteres, {n_secciones} secciones)")
    return True


def _preguntar(mensaje: str, por_defecto: str | None = None, obligatorio: bool = False) -> str:
    sufijo = f" [{por_defecto}]" if por_defecto else ""
    while True:
        try:
            valor = input(f"{mensaje}{sufijo}: ").strip().strip('"').strip("'")
        except (EOFError, KeyboardInterrupt):
            print("\nCancelado.")
            sys.exit(1)
        if valor:
            return valor
        if por_defecto is not None:
            return por_defecto
        if not obligatorio:
            return ""
        print("  Este dato es obligatorio.")


def modo_interactivo() -> tuple[list[Path], str | None, Path | None]:
    """Sin argumentos: pide por terminal el HTML, la URL de origen y la ruta de salida."""
    print("Conversión de HTML guardado en local a Markdown para data/docs/\n")
    while True:
        entrada = Path(_preguntar("Ruta del fichero HTML (p. ej. data/raw/gaming-cpu.html)", obligatorio=True)).expanduser()
        if entrada.exists():
            break
        print(f"  No existe: {entrada}")
    url = _preguntar("URL de origen de la página (Enter para omitir)") or None
    salida_defecto = DOCS_DIR / f"intel_{entrada.stem}.md"
    salida = Path(_preguntar("Ruta del .md de salida", por_defecto=str(salida_defecto))).expanduser()
    if salida.suffix.lower() != ".md":
        salida = salida.with_suffix(".md")
    if salida.exists():
        if _preguntar(f"  {salida} ya existe. ¿Sobrescribir? (s/N)", por_defecto="N").lower() != "s":
            print("Cancelado.")
            sys.exit(1)
    print()
    return [entrada], url, salida


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("html", nargs="*", type=Path, help="fichero(s) HTML guardados en local (sin argumentos: modo interactivo)")
    parser.add_argument("--url", default=None, help="URL de origen a anotar en la cabecera (solo con un fichero)")
    parser.add_argument("--salida", type=Path, default=None, help="fichero .md de salida (solo con un fichero)")
    args = parser.parse_args()

    if args.html:
        entradas, url, salida_forzada = args.html, args.url, args.salida
        if (salida_forzada or url) and len(entradas) > 1:
            parser.error("--salida y --url solo se pueden usar con un único fichero HTML")
    else:
        entradas, url, salida_forzada = modo_interactivo()

    fallos = 0
    for entrada in entradas:
        if not entrada.exists():
            print(f"  No existe: {entrada}")
            fallos += 1
            continue
        salida = salida_forzada or DOCS_DIR / f"intel_{entrada.stem}.md"
        if not convertir_fichero(entrada, salida, url):
            fallos += 1

    if not fallos:
        print("\nRecuerda: al añadir guías cambia el corpus -> python main.py --prepare && python main.py --index --recreate")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
