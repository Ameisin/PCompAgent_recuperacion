"""
Carga de documentos (LOAD): devuelve una lista de `Document` de LangChain
(page_content + metadata) sin trocear ni vectorizar.

Dos tipos de fuente (>= 2 formatos, requisito del corpus):
  1. data/docs/*.md|*.txt|*.pdf  -> loaders de LangChain (una guía = 1 Document, PDF = 1 por página)
  2. data/csv/*.csv              -> patrón manual con pandas: cada fila se convierte en una
                                    frase en lenguaje natural + metadatos.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path

import pandas as pd
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

import config

logger = logging.getLogger(__name__)

## ---------------------------------------------------------------------------
## Tablas de conocimiento derivado (documentadas en data/docs/compatibilidad_componentes.md)
## La información aquí reflejada no se refleja en los .csv, sirve de ampliación de corpus.
## ---------------------------------------------------------------------------
SOCKET_POR_MICROARQUITECTURA = { ## Microarquitectura del procesador -> socket de placa base
    ## AMD
    "Zen 5": "AM5", "Zen 4": "AM5",
    "Zen 3": "AM4", "Zen 2": "AM4", "Zen+": "AM4", "Zen": "AM4",
    "Piledriver": "AM3+", "Bulldozer": "AM3+", "K10": "AM3",
    "Steamroller": "FM2+", "Excavator": "AM4/FM2+",
    ## Intel
    "Arrow Lake": "LGA1851",
    "Raptor Lake Refresh": "LGA1700", "Raptor Lake": "LGA1700", "Alder Lake": "LGA1700",
    "Rocket Lake": "LGA1200", "Comet Lake": "LGA1200",
    "Coffee Lake Refresh": "LGA1151 (chipset serie 300)", "Coffee Lake": "LGA1151 (chipset serie 300)",
    "Kaby Lake": "LGA1151", "Skylake": "LGA1151",
    "Broadwell": "LGA1150", "Haswell Refresh": "LGA1150", "Haswell": "LGA1150",
    "Ivy Bridge": "LGA1155", "Sandy Bridge": "LGA1155",
    "Cascade Lake": "LGA2066",
    "Wolfdale": "LGA775", "Yorkfield": "LGA775", "Core": "LGA775",
}

MEMORIA_POR_SOCKET = { ## Socket de placa base -> tipo de memoria que usa
    "AM5": "DDR5", "LGA1851": "DDR5",
    "LGA1700": "DDR4 o DDR5 (según el modelo de placa)",
    "AM4": "DDR4", "LGA1200": "DDR4", "LGA1151": "DDR4", "LGA1150": "DDR3",
    "LGA1155": "DDR3", "AM3+": "DDR3", "AM3": "DDR3", "FM2+": "DDR3", "LGA775": "DDR2/DDR3",
}

PLACAS_POR_TIPO_CAJA = { ## Tipo de caja -> formatos de placa base que admite (de mayor a menor)
    "ATX Full Tower": "EATX, ATX, Micro ATX y Mini ITX",
    "ATX Mid Tower": "ATX, Micro ATX y Mini ITX",
    "ATX Desktop": "ATX, Micro ATX y Mini ITX",
    "ATX Test Bench": "ATX, Micro ATX y Mini ITX",
    "MicroATX Mid Tower": "Micro ATX y Mini ITX",
    "MicroATX Mini Tower": "Micro ATX y Mini ITX",
    "MicroATX Desktop": "Micro ATX y Mini ITX",
    "MicroATX Slim": "Micro ATX y Mini ITX",
    "Mini ITX Tower": "Mini ITX",
    "Mini ITX Desktop": "Mini ITX",
    "Mini ITX Test Bench": "Mini ITX",
    "HTPC": "Mini ITX (y algunos modelos Micro ATX)",
}

EFICIENCIA_PSU = {
    "plus": "80 PLUS", "bronze": "80 PLUS Bronze", "silver": "80 PLUS Silver",
    "gold": "80 PLUS Gold", "platinum": "80 PLUS Platinum", "titanium": "80 PLUS Titanium",
}


# ---------------------------------------------------------------------------
# Utilidades de formato
# ---------------------------------------------------------------------------
def _es_nulo(valor) -> bool: ## Determina si un valor es None, o float o un str con contenido "", "nan", "0", "0MB".
    if valor is None:
        return True
    if isinstance(valor, float) and math.isnan(valor):
        return True
    return isinstance(valor, str) and valor.strip() in {"", "nan", "0", "0MB"}


def _num(valor, decimales: int = 0) -> str: ## Formatea un número sin ceros de más: 750.0 -> '750', 4.7 -> '4.7'.
    if _es_nulo(valor):
        return ""
    try:
        f = float(valor)
    except (TypeError, ValueError):
        return str(valor)
    if f.is_integer():
        return str(int(f))
    return f"{f:.{decimales}f}" if decimales else str(round(f, 2))


def _precio(valor) -> str: 
    return "" if _es_nulo(valor) else f"{float(valor):.2f} USD"


def _rango(valor, unidad: str) -> str: ## Define un rango o valor: '450,2000' -> '450-2000 rpm'; '1550' -> '1550 rpm'; '0,29' -> 'hasta 29 dB'.
    if _es_nulo(valor):
        return ""
    partes = [p.strip() for p in str(valor).split(",")]
    if len(partes) == 2:
        a, b = partes
        if a in {"0", "0.0"}:
            return f"hasta {_num(b)} {unidad}"
        return f"{_num(a)}-{_num(b)} {unidad}"
    return f"{_num(partes[0])} {unidad}"


def _frase(partes: list[str]) -> str: ## Une fragmentos no vacíos en una descripción legible.
    return " ".join(p.strip() for p in partes if p and p.strip())


## ---------------------------------------------------------------------------
## Plantillas fila -> texto natural (una por categoría). Cada función devuelve
## (texto, metadatos_extra). Los metadatos extra deben ser str/int/float/bool.
## ---------------------------------------------------------------------------
def _fila_cpu(r) -> tuple[str, dict]: ## Para cada CPU recoge: socket, gráficos integrados, turbo, nombre, precio, nº núcleos, microarquitectura y TDP.
    socket = SOCKET_POR_MICROARQUITECTURA.get(str(r["microarchitecture"]), "desconocido")
    graficos = "sin gráficos integrados" if _es_nulo(r["graphics"]) else f"gráficos integrados {r['graphics']}"
    turbo = "" if _es_nulo(r["boost_clock"]) else f"y turbo de {_num(r['boost_clock'], 1)} GHz"
    texto = _frase([
        f"Procesador (CPU) {r['name']}.",
        f"Precio: {_precio(r['price'])}.",
        f"{_num(r['core_count'])} núcleos, frecuencia base de {_num(r['core_clock'], 1)} GHz {turbo}.",
        f"Microarquitectura {r['microarchitecture']}, socket {socket}.",
        f"TDP de {_num(r['tdp'])} W, {graficos}.",
    ])
    meta = {
        "socket": socket,
        "nucleos": int(r["core_count"]),
        "tdp_w": int(r["tdp"]),
        "microarquitectura": str(r["microarchitecture"]),
        "graficos_integrados": not _es_nulo(r["graphics"]),
    }
    return texto, meta


def _fila_gpu(r) -> tuple[str, dict]: ## Para cada GPU recoge:  boost, longitud física, nombre, precio, memoria, frecuencia y color.
    boost = "" if _es_nulo(r["boost_clock"]) else f", boost de {_num(r['boost_clock'])} MHz"
    longitud = "" if _es_nulo(r["length"]) else f"Longitud de {_num(r['length'])} mm (comprobar el espacio disponible en la caja)."
    texto = _frase([
        f"Tarjeta gráfica (GPU) {r['name']}.",
        f"Precio: {_precio(r['price'])}.",
        f"Chip {r['chipset']} con {_num(r['memory'])} GB de memoria de vídeo (VRAM).",
        "" if _es_nulo(r["core_clock"]) else f"Frecuencia base de {_num(r['core_clock'])} MHz{boost}.",
        longitud,
        "" if _es_nulo(r["color"]) else f"Color {r['color']}.",
    ])
    meta = {"chipset": str(r["chipset"]), "vram_gb": float(r["memory"])}
    if not _es_nulo(r["length"]):
        meta["longitud_mm"] = float(r["length"])
    return texto, meta


def _fila_placa_base(r) -> tuple[str, dict]: ## Para cada placa base recoge: socket, tipo de memoria, nombre, precio, formato yt nº de ranuras de memoria.
    socket = str(r["socket"])
    memoria = MEMORIA_POR_SOCKET.get(socket, "")
    texto = _frase([
        f"Placa base {r['name']}.",
        f"Precio: {_precio(r['price'])}.",
        f"Socket {socket}" + (f", memoria {memoria}." if memoria else "."),
        f"Formato {r['form_factor']}.",
        f"{_num(r['memory_slots'])} ranuras de memoria, hasta {_num(r['max_memory'])} GB de RAM.",
        "" if _es_nulo(r["color"]) else f"Color {r['color']}.",
    ])
    meta = {
        "socket": socket,
        "form_factor": str(r["form_factor"]),
        "ranuras_ram": int(r["memory_slots"]),
        "max_ram_gb": int(r["max_memory"]),
    }
    if memoria:
        meta["memoria_tipo"] = memoria
    return texto, meta


def _fila_ram(r) -> tuple[str, dict]: ## Para cada memoria RAM recoge: velocidad, nº de modulos, generación DDR
    gen, mhz = (str(r["speed"]).split(",") + [""])[:2]
    n_mod, gb_mod = (str(r["modules"]).split(",") + [""])[:2]
    total = ""
    try:
        total_gb = int(n_mod) * int(gb_mod)
        total = f"{total_gb} GB en total"
    except ValueError:
        total_gb = 0
    ddr = f"DDR{gen}" if gen else "DDR"
    ppgb = "" if _es_nulo(r["price_per_gb"]) else f"({float(r['price_per_gb']):.2f} USD/GB)"
    texto = _frase([
        f"Memoria RAM {r['name']}.",
        f"Precio: {_precio(r['price'])} {ppgb}.",
        f"{ddr}-{_num(mhz)} MHz, kit de {_num(n_mod)} módulos de {_num(gb_mod)} GB ({total}).",
        f"Latencia CAS {_num(r['cas_latency'])} ({_num(r['first_word_latency'], 2)} ns).",
        "" if _es_nulo(r["color"]) else f"Color {r['color']}.",
    ])
    meta = {"memoria_tipo": ddr, "velocidad_mhz": int(float(mhz)) if mhz else 0, "capacidad_gb": total_gb}
    return texto, meta


def _fila_almacenamiento(r) -> tuple[str, dict]: ## Para cada modelo de almacenamiento recoge: nombre, capacidad en GBm precio por GB, Si es NVM Express o no, si es SSD o HDD, capacidad en GB y factor de forma.
    tipo = str(r["type"])
    if tipo.upper() == "SSD":
        es_nvme = "PCIe" in str(r["interface"])
        desc_tipo = "SSD NVMe" if es_nvme else "SSD"
        tipo_meta = "SSD"
    else:
        desc_tipo = f"Disco duro mecánico (HDD) a {_num(tipo)} rpm"
        tipo_meta = "HDD"
    cap_gb = float(r["capacity"])
    cap_txt = f"{cap_gb / 1000:g} TB" if cap_gb >= 1000 else f"{_num(cap_gb)} GB"
    ff = str(r["form_factor"])
    if ff in {"2.5", "3.5"}:
        ff = f"{ff} pulgadas"
    ppgb = "" if _es_nulo(r["price_per_gb"]) else f"({float(r['price_per_gb']):.3f} USD/GB)"
    texto = _frase([
        f"Almacenamiento {r['name']}.",
        f"Precio: {_precio(r['price'])} {ppgb}.",
        f"{desc_tipo} de {cap_txt}, formato {ff}, interfaz {r['interface']}.",
        "" if _es_nulo(r["cache"]) else f"Caché de {_num(r['cache'])} MB.",
    ])
    meta = {"tipo_disco": tipo_meta, "capacidad_gb": cap_gb, "interfaz": str(r["interface"]), "form_factor": str(r["form_factor"])}
    return texto, meta


def _fila_fuente(r) -> tuple[str, dict]: ## Para cada modelo de fuente de alimentación recoge: nombre, precio, vatios de potencia, certificado de eficiencia y tipo de modularidad
    eficiencia = EFICIENCIA_PSU.get(str(r["efficiency"]).lower(), "sin certificación 80 PLUS")
    modular = {"Full": "totalmente modular", "Semi": "semimodular", "false": "no modular"}.get(
        str(r["modular"]), str(r["modular"])
    )
    texto = _frase([
        f"Fuente de alimentación (PSU) {r['name']}.",
        f"Precio: {_precio(r['price'])}.",
        f"{_num(r['wattage'])} W de potencia, certificación {eficiencia}, formato {r['type']}, cableado {modular}.",
        "" if _es_nulo(r["color"]) else f"Color {r['color']}.",
    ])
    meta = {"potencia_w": int(r["wattage"]), "eficiencia": eficiencia, "form_factor": str(r["type"]), "modular": modular}
    return texto, meta


def _fila_caja(r) -> tuple[str, dict]: ## Para cada modelo de caja recoge: nombre, precio, tipo, panel lateral, volumen exterior, número de bahías internas y color.
    tipo = str(r["type"])
    placas = PLACAS_POR_TIPO_CAJA.get(tipo, "")
    fuente = "no incluye fuente de alimentación" if _es_nulo(r["psu"]) else f"incluye fuente de {_num(r['psu'])} W"
    texto = _frase([
        f"Caja (chasis) {r['name']}.",
        f"Precio: {_precio(r['price'])}.",
        f"Tipo {tipo}" + (f", admite placas base {placas}." if placas else "."),
        "" if _es_nulo(r["side_panel"]) else f"Panel lateral de {r['side_panel']}.",
        "" if _es_nulo(r["external_volume"]) else f"Volumen exterior de {_num(r['external_volume'], 1)} litros.",
        f"{_num(r['internal_35_bays'])} bahías internas de 3.5 pulgadas; {fuente}.",
        "" if _es_nulo(r["color"]) else f"Color {r['color']}.",
    ])
    meta = {"tipo_caja": tipo, "incluye_fuente": not _es_nulo(r["psu"])}
    if placas:
        meta["placas_admitidas"] = placas
    return texto, meta


def _fila_disipador(r) -> tuple[str, dict]: ## Para cada modelo de disipador recoge: nombre, precio, tipo, velocidad en RPM, ruido y color.
    liquida = not _es_nulo(r["size"])
    tipo = f"refrigeración líquida AIO con radiador de {_num(r['size'])} mm" if liquida else "refrigeración por aire"
    texto = _frase([
        f"Disipador de CPU {r['name']}.",
        f"Precio: {_precio(r['price'])}.",
        f"Tipo: {tipo}.",
        "" if _es_nulo(r["rpm"]) else f"Velocidad {_rango(r['rpm'], 'rpm')}.",
        "" if _es_nulo(r["noise_level"]) else f"Ruido {_rango(r['noise_level'], 'dB')}.",
        "" if _es_nulo(r["color"]) else f"Color {r['color']}.",
    ])
    meta: dict[str, object] = {"tipo_refrigeracion": "liquida" if liquida else "aire"}
    if liquida:
        meta["radiador_mm"] = int(float(r["size"]))
    return texto, meta


def _fila_ventilador(r) -> tuple[str, dict]: ## Para cada modelo de ventilar recoge: nombre, precio, tamaño, velocidad, caudal, ruido y color.
    pwm = "con control PWM" if str(r["pwm"]).lower() == "true" else "sin PWM (voltaje fijo)"
    texto = _frase([
        f"Ventilador de caja {r['name']}.",
        f"Precio: {_precio(r['price'])}.",
        f"Tamaño {_num(r['size'])} mm, {pwm}.",
        "" if _es_nulo(r["rpm"]) else f"Velocidad {_rango(r['rpm'], 'rpm')}.",
        "" if _es_nulo(r["airflow"]) else f"Caudal {_rango(r['airflow'], 'CFM')}.",
        "" if _es_nulo(r["noise_level"]) else f"Ruido {_rango(r['noise_level'], 'dB')}.",
        "" if _es_nulo(r["color"]) else f"Color {r['color']}.",
    ])
    return texto, {"tamano_mm": int(r["size"])}


def _fila_pasta_termica(r) -> tuple[str, dict]: ## Para cada modelo de pasta térmica recoge: nombre, precio y cantidad.
    texto = _frase([f"Pasta térmica {r['name']}.", f"Precio: {_precio(r['price'])}.", f"Cantidad: {_num(r['amount'], 1)} g."])
    return texto, {}


def _fila_tarjeta_sonido(r) -> tuple[str, dict]: ## Para cada modelo de tarjeta de sonido recoge: nombre, precio, canales, interfaz, relación señal /ruido, frecuencia de muestreo y chipset.
    texto = _frase([
        f"Tarjeta de sonido {r['name']}.",
        f"Precio: {_precio(r['price'])}.",
        f"{r['channels']} canales, interfaz {r['interface']}.",
        "" if _es_nulo(r["snr"]) else f"Relación señal/ruido {_num(r['snr'])} dB.",
        "" if _es_nulo(r["sample_rate"]) else f"Frecuencia de muestreo {_num(r['sample_rate'])} kHz.",
        "" if _es_nulo(r["chipset"]) else f"Chipset {r['chipset']}.",
    ])
    return texto, {"interfaz": str(r["interface"])}


def _fila_tarjeta_red(r) -> tuple[str, dict]: ## Para cad amodelo de tarjeta de red recoge: nombre, precio, protocolo, interfaz y color.
    texto = _frase([
        f"Tarjeta de red inalámbrica {r['name']}.",
        f"Precio: {_precio(r['price'])}.",
        f"Protocolo {r['protocol']}, interfaz {r['interface']}.",
        "" if _es_nulo(r["color"]) else f"Color {r['color']}.",
    ])
    return texto, {"protocolo": str(r["protocol"]), "interfaz": str(r["interface"])}


PLANTILLAS = { ## Se recogen todas las filas
    "cpu": _fila_cpu,
    "gpu": _fila_gpu,
    "placa_base": _fila_placa_base,
    "ram": _fila_ram,
    "almacenamiento": _fila_almacenamiento,
    "fuente": _fila_fuente,
    "caja": _fila_caja,
    "disipador": _fila_disipador,
    "ventilador": _fila_ventilador,
    "pasta_termica": _fila_pasta_termica,
    "tarjeta_sonido": _fila_tarjeta_sonido,
    "tarjeta_red": _fila_tarjeta_red,
}


## ---------------------------------------------------------------------------
## Loaders de CSV
## ---------------------------------------------------------------------------
def _ruta_relativa(ruta: Path) -> str:
    """`source` legible y estable en cualquier máquina: 'data/csv/cpu.csv'."""
    try:
        return ruta.resolve().relative_to(config.BASE_DIR).as_posix()
    except ValueError:
        return ruta.name


def cargar_csv_componentes(ruta: Path, categoria: str, nombre_categoria: str) -> list[Document]: ## Convierte cada fila del .csv de una categoría en un documento en lenguaje natural.
    plantilla = PLANTILLAS[categoria]
    df = pd.read_csv(ruta)
    total = len(df)
    if config.SOLO_CON_PRECIO and "price" in df.columns:
        df = df[df["price"].notna()]
    if config.MAX_FILAS_POR_CSV:
        df = df.head(config.MAX_FILAS_POR_CSV)

    documentos: list[Document] = []
    for _, fila in df.iterrows():
        if _es_nulo(fila.get("name")):
            continue
        try:
            texto, extra = plantilla(fila)
        except (KeyError, ValueError, TypeError) as exc:  # fila corrupta: se omite y se avisa
            logger.warning("Fila omitida en %s (%s): %s", ruta.name, fila.get("name"), exc)
            continue
        metadata = {
            "source": _ruta_relativa(ruta),
            "tipo": "componente",
            "categoria": categoria,
            "categoria_nombre": nombre_categoria,
            "nombre": str(fila["name"]),
            "precio_usd": float(fila["price"]) if not _es_nulo(fila.get("price")) else -1.0,
            **extra,
        }
        documentos.append(Document(page_content=texto, metadata=metadata))

    logger.info("  %-28s %5d filas -> %4d documentos", ruta.name, total, len(documentos))
    return documentos


def _fila_videojuego(r) -> str: ## Determina para cada juego los requisitos mínimos, recomendados y el año de lanzamiento.
    def cpu(prefijo: str) -> str:
        if _es_nulo(r[f"{prefijo}_CPU_CPU_Speed"]):
            return ""
        nucleos = r[f"{prefijo}_CPU_Physical_Cores"]
        return f"CPU de {_num(nucleos)} núcleos a {_num(r[f'{prefijo}_CPU_CPU_Speed'], 2)} GHz"

    def gpu(prefijo: str) -> str:
        mem = r[f"{prefijo}_GPU_Memory"]
        if _es_nulo(mem):
            return ""
        return f"GPU con {float(mem) / 1024:g} GB de VRAM"

    def lista(items: list[str]) -> str:
        return ", ".join(i for i in items if i)

    minimos = lista([
        cpu("Min"),
        f"{r['Min_RAM']} de RAM",
        gpu("Min"),
        "" if _es_nulo(r["Min_HDD_Space"]) else f"{r['Min_HDD_Space']} de espacio en disco",
        "" if _es_nulo(r["Min_OS"]) else str(r["Min_OS"]),
        "" if _es_nulo(r["Min_Direct_X"]) else f"DirectX {_num(r['Min_Direct_X'])}",
    ])
    recomendados = lista([
        cpu("Recom"),
        "" if _es_nulo(r["Recom_RAM"]) else f"{r['Recom_RAM']} de RAM",
        gpu("Recom"),
        "" if _es_nulo(r["Recom_GPU_PSU"]) else f"fuente de alimentación de al menos {_num(r['Recom_GPU_PSU'])} W",
        "" if _es_nulo(r["Recom_OS"]) else str(r["Recom_OS"]),
    ])
    ano = str(r["Release_Date"])[:4]
    return _frase([
        f"Videojuego {r['Name']} (lanzado en {ano}).",
        f"Requisitos mínimos para jugar: {minimos}.",
        f"Requisitos recomendados para el mejor rendimiento: {recomendados}." if recomendados else "",
    ])


def cargar_csv_videojuegos(ruta: Path) -> list[Document]: ## csv de requisitos de videojuegos: una fila = juego = documento"
    """CSV de requisitos de videojuegos: una fila = un juego = un Document."""
    df = pd.read_csv(ruta)
    total = len(df)
    df = df[df["Name"].notna() & df["Min_CPU_CPU_Speed"].notna()]
    df = df[~df["Min_RAM"].astype(str).isin(["0", "0MB"])]
    df = df[df["Min_CPU_Physical_Cores"].fillna(0) <= 32]  ## filas corruptas (p. ej. 41 núcleos)
    df = df.assign(_anio=pd.to_numeric(df["Release_Date"].astype(str).str[:4], errors="coerce"))
    df = df[df["_anio"] >= config.ANIO_MIN_VIDEOJUEGOS]
    df = df.sort_values("Release_Date", ascending=False).drop_duplicates("Name")
    if config.MAX_FILAS_VIDEOJUEGOS:
        df = df.head(config.MAX_FILAS_VIDEOJUEGOS)

    documentos = []
    for _, fila in df.iterrows():
        metadata = {
            "source": _ruta_relativa(ruta),
            "tipo": "videojuego",
            "categoria": "videojuego",
            "categoria_nombre": "Videojuego",
            "nombre": str(fila["Name"]),
            "anio": int(fila["_anio"]),
            "ram_min": str(fila["Min_RAM"]),
        }
        documentos.append(Document(page_content=_fila_videojuego(fila), metadata=metadata))
    logger.info("  %-28s %5d filas -> %4d documentos", ruta.name, total, len(documentos))
    return documentos


## ---------------------------------------------------------------------------
## Loaders de texto (guías)
## ---------------------------------------------------------------------------
def cargar_archivo_texto(ruta: Path) -> list[Document]: ## Recoge el archivo, carga el contenido, lo parsea y añade metadatos.
    sufijo = ruta.suffix.lower()
    if sufijo == ".pdf":
        docs = PyPDFLoader(str(ruta)).load()
    elif sufijo in {".txt", ".md"}:
        docs = TextLoader(str(ruta), encoding="utf-8").load()
    else:
        logger.warning("  Formato no soportado, se ignora: %s", ruta.name)
        return []
    for d in docs:
        d.metadata.update({
            "source": _ruta_relativa(ruta),
            "tipo": "guia",
            "categoria": "guia",
            "categoria_nombre": "Guía de montaje y compatibilidad",
            "nombre": ruta.stem,
        })
        ## PyPDFLoader guarda 'page' 0-indexed; lo pasamos a 1-indexed para citar
        if "page" in d.metadata:
            d.metadata["page"] = int(d.metadata["page"]) + 1
    logger.info("  %-28s -> %4d documentos", ruta.name, len(docs))
    return docs


def cargar_carpeta_docs(carpeta: Path = config.DOCS_DIR) -> list[Document]: ## Carga recursivamente los archivos de texto/PDF de la carpeta (ignora ocultos).
    documentos: list[Document] = []
    if not carpeta.exists():
        logger.warning("No existe la carpeta de guías: %s", carpeta)
        return documentos
    for ruta in sorted(carpeta.rglob("*")):
        if ruta.is_file() and not ruta.name.startswith("."):
            documentos.extend(cargar_archivo_texto(ruta))
    return documentos


## ---------------------------------------------------------------------------
## Punto de entrada
## ---------------------------------------------------------------------------
def cargar_documentos() -> list[Document]: ## Carga todo el corpus: guías (texto) + csv de componentes + csv de videojuegos.
    logger.info("Cargando guías desde %s", config.ruta_corta(config.DOCS_DIR))
    documentos = cargar_carpeta_docs()

    logger.info("Cargando CSV desde %s (solo_con_precio=%s, max_filas_por_csv=%s)",
                config.ruta_corta(config.CSV_DIR), config.SOLO_CON_PRECIO, config.MAX_FILAS_POR_CSV)
    for nombre_fichero, (categoria, nombre_cat) in config.CATEGORIAS_CSV.items():
        ruta = config.CSV_DIR / nombre_fichero
        if not ruta.exists():
            logger.warning("  No encontrado, se omite: %s", nombre_fichero)
            continue
        documentos.extend(cargar_csv_componentes(ruta, categoria, nombre_cat))

    ruta_juegos = config.CSV_DIR / config.CSV_VIDEOJUEGOS
    if ruta_juegos.exists():
        documentos.extend(cargar_csv_videojuegos(ruta_juegos))
    else:
        logger.warning("  No encontrado, se omite: %s", config.CSV_VIDEOJUEGOS)

    logger.info("Total documentos LangChain: %d | caracteres: %d",
                len(documentos), sum(len(d.page_content) for d in documentos))
    return documentos
