import config as cfg
from pathlib import Path
import pandas as pd

from load import SOCKET_POR_MICROARQUITECTURA

MAPEO = {
    "nombre": "name",        # columnas reales de los CSV de PCPartPicker
    "tipo": "tipo",          # cpu, gpu, ram...
    "precio": "price",
    "stock": "stock",
    "url": "url",
    "tienda": "tienda",
}

USES = ["gaming", "edicion_video", "programacion", "ia", "ofimatica", "streaming"]

tool_componentes = {
    
    "name": "buscar_componentes",
    "description": "Busca componentes de PC por tipo y rango de precio en euros. "
                   "Devuelve hasta 10 resultados ordenados de más barato a más caro.",
    "input_schema": {
        "type": "object",
        "properties": {
            "componente": {"type": "string",
                           "description": "Tipo: cpu, gpu, ram, placa, fuente, caja, ssd..."},
            "precio_min": {"type": "number", "description": "Precio mínimo en euros"},
            "precio_max": {"type": "number", "description": "Precio máximo en euros"},
        },
        "required": ["componente"],
    },   
}

tool_split = {
    
    "name": "split_budget",
    "description": "Reparte un presupuesto total entre los componentes segun el uso principal. Util para empezar una build.",
        "input_schema": {
            "type": "object",
            "properties": {
                "total_budget": {"type": "number", "description": "Presupuesto total."},
                "use_case": {"type": "string", "enum": USES},
            },
            "required": ["total_budget", "use_case"],
        },
    
}

tool_totalCalc = {
    
    "name": "calculate_build_total",
        "description": "Suma los precios de los componentes elegidos, aplica IVA opcional y dice cuanto queda (o se pasa) respecto al presupuesto.",
        "input_schema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}, "price": {"type": "number"}},
                        "required": ["name", "price"],
                    },
                },
                "budget": {"type": "number", "description": "Presupuesto del usuario (opcional)."},
                "vat_percent": {"type": "number", "description": "IVA a aplicar si los precios no lo incluyen (21 en Espana). 0 si ya incluido.", "default": 0},
            },
            "required": ["items"],
        },
    
}

tool_ram = {
    
    "name": "recommend_ram_storage",
        "description": "Recomienda capacidad minima y recomendada de RAM y almacenamiento segun el uso.",
        "input_schema": {
            "type": "object",
            "properties": {"use_case": {"type": "string", "enum": USES}},
            "required": ["use_case"],
        },
}

tool_monitor = {
    
    "name": "recommend_monitor",
        "description": "Sugiere resolucion y tasa de refresco de monitor segun el uso y el nivel de GPU previsto.",
        "input_schema": {
            "type": "object",
            "properties": {
                "use_case": {"type": "string", "enum": USES},
                "gpu_tier": {"type": "string", "enum": ["basica", "media", "alta"], "description": "Nivel aproximado de la GPU."},
            },
            "required": ["use_case", "gpu_tier"],
        },
}

_SPLITS = {
    "gaming":        {"GPU": 38, "CPU": 17, "Placa base": 10, "RAM": 7, "Almacenamiento": 8, "Fuente": 8, "Caja": 6, "Refrigeracion": 6},
    "edicion_video": {"GPU": 28, "CPU": 25, "Placa base": 10, "RAM": 10, "Almacenamiento": 10, "Fuente": 7, "Caja": 5, "Refrigeracion": 5},
    "programacion":  {"GPU": 10, "CPU": 28, "Placa base": 12, "RAM": 15, "Almacenamiento": 14, "Fuente": 7, "Caja": 7, "Refrigeracion": 7},
    "ia":            {"GPU": 45, "CPU": 13, "Placa base": 10, "RAM": 10, "Almacenamiento": 8, "Fuente": 8, "Caja": 3, "Refrigeracion": 3},
    "ofimatica":     {"GPU": 0,  "CPU": 30, "Placa base": 15, "RAM": 15, "Almacenamiento": 18, "Fuente": 8, "Caja": 7, "Refrigeracion": 7},
    "streaming":     {"GPU": 32, "CPU": 22, "Placa base": 10, "RAM": 9, "Almacenamiento": 9, "Fuente": 7, "Caja": 5, "Refrigeracion": 6},
}

_RAM_STORAGE = {
    "gaming":        {"ram_min_gb": 16, "ram_rec_gb": 32, "storage_min": "500 GB SSD NVMe", "storage_rec": "1 TB SSD NVMe"},
    "edicion_video": {"ram_min_gb": 32, "ram_rec_gb": 64, "storage_min": "1 TB SSD NVMe", "storage_rec": "2 TB NVMe + disco de datos"},
    "programacion":  {"ram_min_gb": 16, "ram_rec_gb": 32, "storage_min": "500 GB SSD NVMe", "storage_rec": "1 TB SSD NVMe"},
    "ia":            {"ram_min_gb": 32, "ram_rec_gb": 64, "storage_min": "1 TB SSD NVMe", "storage_rec": "2 TB SSD NVMe (los modelos ocupan mucho)"},
    "ofimatica":     {"ram_min_gb": 8,  "ram_rec_gb": 16, "storage_min": "256 GB SSD", "storage_rec": "512 GB SSD NVMe"},
    "streaming":     {"ram_min_gb": 16, "ram_rec_gb": 32, "storage_min": "1 TB SSD NVMe", "storage_rec": "1 TB NVMe + disco para grabaciones"},
}



def cargar_data(carpeta: Path = cfg.CSV_DIR) -> pd.DataFrame:
    # Solo el catálogo de config.CATEGORIAS_CSV (no videojuegos ni JSON de fallback);
    # el tipo es el slug de categoría del RAG: cpu, gpu, placa_base, ram...
    frames = []
    for archivo, (slug, _nombre) in cfg.CATEGORIAS_CSV.items():
        f = Path(carpeta) / archivo
        if not f.exists():
            continue
        df = pd.read_csv(f)
        df["_archivo"] = f.name
        df["tipo"] = slug
        if slug == "cpu":  # el CSV no trae socket: misma tabla derivada que usa el RAG (load.py)
            df["socket"] = df["microarchitecture"].map(SOCKET_POR_MICROARQUITECTURA)
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    return df.rename(columns={v: k for k, v in MAPEO.items() if v in df.columns})

# Cargar UNA vez al arrancar
DF = cargar_data()
DF["precio"] = pd.to_numeric(DF["precio"], errors="coerce")
DF = DF.dropna(subset=["precio"])          # descarta filas sin precio válido
DF["_busqueda"] = DF["nombre"].astype(str).str.lower()

def buscar_precio(componente: str, precio_min: float = 0, precio_max: float | None = None) -> dict:
    
    
    if precio_max is not None and precio_min > precio_max:
        return {"error": f"precio_min ({precio_min}) es mayor que precio_max ({precio_max})"}
    
    df = DF[DF["tipo"] == componente.lower()]
    if df.empty:
        return {"error": f"Componente '{componente}' no existe",
                "componentes_validos": sorted(DF["tipo"].unique())}
        
    df = df[df["precio"] >= precio_min]
    if precio_max is not None:
        df = df[df["precio"] <= precio_max]
        
    if df.empty:
        base = DF[DF["tipo"] == componente.lower()]["precio"]
        return {"total": 0,
                "mensaje": "Ningún resultado en ese rango",
                "rango_real": {"min": float(base.min()), "max": float(base.max())}}
        
    df = df.sort_values("precio")
    cols = [c for c in df.columns if not c.startswith("_") and c != "tipo"]
    # specs de la categoría (socket, memoria...) sin las columnas vacías de las demás categorías
    filas = [{k: v for k, v in r.items() if pd.notna(v)} for r in df.head(10)[cols].to_dict(orient="records")]
    return {"total": len(df), "resultados": filas}
    
    
def split_budget(total_budget, use_case):
    pct = _SPLITS[use_case]
    return {
        "use_case": use_case,
        "split": {k: {"percent": v, "amount": round(total_budget * v / 100)} for k, v in pct.items() if v > 0},
        "note": "Reparto orientativo: ajustalo segun precios reales y preferencias del usuario.",
    }
    

def calculate_build_total(items, budget=None, vat_percent=0):
    subtotal = sum(i["price"] for i in items)
    total = subtotal * (1 + vat_percent / 100)
    result = {"subtotal": round(subtotal, 2), "vat_percent": vat_percent, "total": round(total, 2)}
    if budget is not None:
        diff = budget - total
        result["budget"] = budget
        result["remaining"] = round(diff, 2)
        result["within_budget"] = diff >= 0
    result["note"] = "Los precios cambian: confirmalos en tienda."
    return result



def recommend_ram_storage(use_case):
    return {"use_case": use_case, **_RAM_STORAGE[use_case],
            "note": "Prefiere 2 modulos (dual channel) en lugar de uno solo."}
    
    
    
def recommend_monitor(use_case, gpu_tier):
    if use_case == "ofimatica":
        return {"resolution": "1080p", "refresh_hz": 60, "reason": "Para trabajo basta; prioriza panel IPS y buen confort visual."}
    if use_case in ("edicion_video", "programacion"):
        return {"resolution": "1440p", "refresh_hz": 60,
                "reason": "Mas espacio de trabajo; prioriza panel IPS con buena fidelidad de color."}
    table = {
        "basica": ("1080p", 60, "Con GPU basica, 1080p a 60 Hz es lo realista."),
        "media":  ("1080p" if use_case == "streaming" else "1440p", 144, "Equilibrio entre nitidez y fluidez."),
        "alta":   ("1440p", 165, "4K es posible, pero 1440p de alta tasa suele dar mejor experiencia/precio."),
    }
    res, hz, why = table[gpu_tier]
    return {"resolution": res, "refresh_hz": hz, "reason": why}



TOOL_FUNCTIONS = {
    "buscar_componentes": buscar_precio,   # mismo nombre que su esquema tool_componentes
    "split_budget": split_budget,
    "calculate_build_total": calculate_build_total,
    "recommend_ram_storage": recommend_ram_storage,
    "recommend_monitor": recommend_monitor,
}

def run_tool(name, tool_input):
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"Tool desconocida: {name}"}
    try:
        return fn(**tool_input)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}