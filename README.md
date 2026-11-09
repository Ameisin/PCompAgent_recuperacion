![!\[Cabecera\](./assets/cabecera_thebridge.png)](assets/cabecera_thebridge.png)

# Asistente PcComponentes

<p align="left">
<img src="https://img.shields.io/badge/STATUS-EN%20DESARROLLO-green">
</p> 

[![GitHub stars](https://img.shields.io/github/stars/Ameisin?style=for-the-badge&label=Estrellas&logo=github)](https://github.com/Ameisin/PCompAgent)


## Índice
* [Descripción del proyecto](#descripción-del-proyecto)
* [Características de la aplicación](#Características-de-la-aplicación)
* [Acceso al proyecto](#acceso-proyecto)
* [Project Break 2: agente multiagente](#project-break-2-agente-multiagente-langgraph)
* [Tecnologías utilizadas](#tecnologías-utilizadas)
* [Desarrolladores del Proyecto](#desarrolladores-del-proyecto)
* [Conclusión](#conclusión)

## Descripción del proyecto
**PCompAgent** es un asistente conversacional basado en RAG (Retrieval-Augmented Generation) para ayudar a elegir componentes de PC por piezas: procesador, tarjeta gráfica, placa base, memoria, almacenamiento, fuente de alimentación, caja y refrigeración. Responde preguntas sobre características, precios orientativos, compatibilidad entre piezas (socket, tipo de memoria, formato de placa y caja) y requisitos de videojuegos, apoyándose únicamente en un corpus propio indexado en una base vectorial.

El sistema sigue una arquitectura RAG completa:

1. **Pipeline offline**: carga del corpus, limpieza, chunking, generación de embeddings e indexación persistente en ChromaDB.
2. **Pipeline online**: la pregunta del usuario se vectoriza, se recuperan los *top-k* fragmentos más similares y un LLM (Gemini) redacta la respuesta usando solo ese contexto. Si el corpus no contiene la evidencia necesaria, el asistente se abstiene en lugar de inventar.

El corpus combina dos formatos:

- **CSV** con el catálogo de componentes (12 categorías) y un CSV de requisitos mínimos y recomendados de videojuegos. Cada fila se convierte en una frase en lenguaje natural con metadatos (categoría, socket, precio, etc.).
- **Markdown** con guías de compra y montaje (elección de CPU, RAM, placa base, fuente, SSD, refrigeración y una guía de montaje de PC gaming).

Este proyecto es la primera pieza de un proyecto incremental: el RAG expone una API interna (`responder(pregunta) -> dict`) independiente de la interfaz, pensada para reutilizarse como *tool* en fases posteriores.

## Características de la aplicación
### Asistente
- **Respuestas ancladas al corpus**: el LLM solo utiliza los fragmentos recuperados y cita la fuente de cada dato.
- **Abstención**: ante preguntas fuera de dominio (geografía, productos inexistentes, benchmarks no indexados) el asistente indica que no tiene esa información en lugar de inventar.
- **Compatibilidad entre piezas**: el corpus incluye tablas derivadas (microarquitectura → socket, socket → tipo de memoria, tipo de caja → formatos de placa admitidos) que enriquecen cada fila de componente.
- **Requisitos de videojuegos**: requisitos mínimos y recomendados de más de 2.000 juegos publicados desde 2019.

### Procesamiento de datos
Un área de los datos del corpus ha sido procesada para **favorecer la eficiencia en el consumo de tokens** del modelo LLM. 

Los datos se han obtenido de la **[página web oficial de Intel](https://www.intel.la/content/www/xl/es/gaming/resources/how-to-build-a-gaming-pc.html)**. Se han descargado todas las páginas con contenido relevante para el proyecto en formato **HTML**. Después, se ha desarrollado un script, `convertir_html_a_markdown`, para **convertir todos los archivos en HTML a Markdown**. 

El modelo LLM podría leer el archivo en formato HTML, pero además de leer la información crucial, leería toda la información del estilo visual, la estructura y semántica compleja, multimedia y recursos emebebidos, scripsts, metadatos y comportamiento. Esa información no es útil, **podría encaminar a errores** y sobre todo, **costar más cantidad de tokens de lectura** de los necesarios. 

### Interfaz Streamlit (`streamlit run app.py`)
Desde el PB2, la interfaz es cliente del agente multiagente (ver [Project Break 2](#project-break-2-agente-multiagente-langgraph)):
- Chat con historial; cada mensaje es un turno del grafo (`procesar_turno`).
- Barra lateral: `max_steps`, `max_turns`, `thread_id`, botón "Nueva conversación" (nuevo `thread_id`).
- HITL: cuando hay un plan, el chat se bloquea y aparecen los botones Aprobar y Rechazar (con motivo opcional).
- Expander de depuración: log del supervisor, traza de tools, traza por turno, checkpoints e indicadores HITL y `done`.

El RAG del PB1 sigue disponible sin interfaz con `python main.py --ask "pregunta"`.

### CLI (`python main.py`)
| Comando | Descripción |
|---|---|
| `python main.py` | Indexa el corpus si aún no existe el índice y abre la interfaz Streamlit |
| `python main.py --prepare` | Carga, limpia, fragmenta y vectoriza el corpus (`output/embeddings.json`) |
| `python main.py --index [--recreate-index]` | Indexa los embeddings en ChromaDB; con `--recreate-index` regenera la colección desde cero |
| `python main.py --query "pregunta" [--top-k N]` | Solo retrieval: muestra los fragmentos recuperados y su contexto |
| `python main.py --ask "pregunta" [--top-k N]` | RAG completo: respuesta del LLM con fuentes y métricas |
| `python main.py --eval` | Barrido de varios valores de K sobre las preguntas de evaluación |

### Configuración centralizada (`config.py`)
Todos los parámetros ajustables viven en un único fichero: rutas, categorías de CSV, filtros del corpus, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `MAX_CHUNKS`, proveedor y modelo de embeddings, `TOP_K`, modelo y temperatura de generación. Algunos pueden sobrescribirse por variable de entorno (`EMBEDDING_PROVIDER`, `MAX_CHUNKS`, `MAX_FILAS_POR_CSV`, `ESTRATEGIA_CHUNKING`).

> ⚠️ Si cambias el modelo de embeddings, `CHUNK_SIZE` o `MAX_CHUNKS`, regenera el índice con `python main.py --recreate-index`.

## Acceso al proyecto
### Requisitos

- **Python 3.10 o superior** (el proyecto se ha desarrollado con Python 3.14).
- **Git** para clonar el repositorio.
- **Clave de API de Gemini** (Google AI Studio). Es necesaria para generar embeddings y respuestas. Puedes obtenerla en https://aistudio.google.com/apikey.
- Conexión a internet para llamar a la API de Gemini.
- Opcional: si prefieres embeddings locales sin API, instala `sentence-transformers` y usa `EMBEDDING_PROVIDER=huggingface` (requiere varios GB de dependencias).

### Entorno virtual

1. Clona el repositorio:

   ```bash
   git clone https://github.com/Ameisin/PCompAgent.git
   cd PCompAgent
   ```

2. Crea y activa el entorno virtual.

   Windows (PowerShell):
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   Linux / macOS:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Instala las dependencias:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Configura la clave de API. Copia la plantilla y edita el fichero `.env` con tu clave:

   ```bash
   cp .env.example .env
   ```

   Contenido de `.env`:
   ```
   GEMINI_API_KEY=tu_clave_aqui
   ```

   > El fichero `.env` está en `.gitignore` y nunca debe subirse al repositorio.

5. Genera el índice la primera vez (tarda unos minutos porque vectoriza todo el corpus):

   ```bash
   python main.py --prepare
   python main.py --index --recreate-index
   ```

6. Prueba el asistente desde la terminal o abre la interfaz:

   ```bash
   python main.py --ask "¿Qué socket usa un procesador Ryzen 7 7700X?"
   streamlit run app.py
   ```

   También puedes ejecutar simplemente `python main.py`: si no existe el índice lo construye y a continuación abre Streamlit.

### Estructura del proyecto

```
PCompAgent/
├── README.md
├── requirements.txt
├── .env.example                 # plantilla de variables de entorno
├── .gitignore
├── config.py                    # configuración centralizada
├── main.py                      # CLI: prepare / index / query / ask / eval
├── app.py                       # interfaz Streamlit
│
├── load.py                      # carga del corpus (CSV -> frases, Markdown/PDF -> Document)
├── clean.py                     # normalización de texto
├── chunk.py                     # fragmentación (Markdown por encabezados, CSV atómico)
├── embed.py                     # embeddings Gemini / Hugging Face + caché
├── index.py                     # indexación en ChromaDB
├── retrieve.py                  # retrieval top-k
├── context.py                   # formateo del contexto recuperado
├── prompt.py                    # plantilla del prompt RAG
├── generate_rep.py              # llamada al LLM (Gemini)
├── logic.py                     # API interna: responder(pregunta) -> dict
├── eval_retrival.py             # evaluación de retrieval con varios K
├── gemini_auto.py               # carga de la API key
├── verificar.py                 # comprobaciones automáticas
├── convertir_html_a_markdown.py # utilidad para añadir guías al corpus
│
├── data/
│   ├── csv/                     # catálogo de componentes + requisitos de videojuegos
│   └── md/                      # guías de compra y montaje en Markdown
├── queries/
│   └── preguntas_eval.json      # set de preguntas de evaluación
├── entregables/
│   └── informe_decisiones.md    # informe final del equipo
├── output/                      # embeddings.json y logs (gitignored, se regenera)
└── chroma/                      # índice ChromaDB persistente (gitignored, se regenera)
```

### Fuentes del corpus

| Fuente | Formato | Contenido | Enlace |
|---|---|---|---|
| Dataset de componentes de PC (PCPartPicker) | CSV | 12 categorías de componentes con precio y especificaciones | [PCPartPicker](https://www.kaggle.com/datasets/baraazaid/pc-video-game-requirements-v2) |
| Dataset de requisitos de videojuegos | CSV | Requisitos mínimos y recomendados por juego | [Kaggle](https://www.kaggle.com/datasets/baraazaid/pc-video-game-requirements-v2) |
| Guías de compra y montaje | Markdown | 7 guías (CPU, RAM, placa base, fuente, SSD, refrigeración, montaje) | [Intel](https://www.intel.la/content/www/xl/es/gaming/resources/how-to-build-a-gaming-pc.html) |

Todos los datos son públicos y se utilizan con fines educativos.

### Preguntas de ejemplo

- ¿Qué socket usa el procesador AMD Ryzen 7 7700X y qué tipo de memoria necesita?
- ¿Qué placas base admite una caja ATX Mid Tower?
- ¿Cuántos vatios recomienda la guía para una fuente de alimentación en un PC gaming?
- ¿Qué requisitos recomendados tiene Cyberpunk 2077?
- ¿Cuál es la capital de Francia? *(fuera de corpus: el asistente debe abstenerse)*

## Project Break 2: agente multiagente (LangGraph)

El agente es un asesor de compra de PC. A partir del uso y el presupuesto propone una configuración con piezas reales del catálogo, comprueba compatibilidad y precio, y no la da por cerrada hasta que una persona la aprueba (HITL).

Reutilizamos el RAG completo del PB1 (corpus CSV y Markdown, ChromaDB, Gemini y abstención). La tool `RAG_consultar_catalogo` llama a su API interna `logic.responder()`, así que no hay un segundo RAG.

El agente resuelve configuraciones por presupuesto y uso, piezas sueltas, compatibilidad, requisitos de videojuegos, conversión de moneda y lectura de una ficha técnica en imagen. No da precios en tiempo real de tiendas ni hace compras, y si la pregunta no es del dominio lo dice en lugar de inventar.

### Grafo

```text
START -> supervisor --+-- requisitos ---+
                      +-- componentes --+--> supervisor -> ...
                      +-- sintetizar ---+
                FINISH --+-- aplicar (pausa: la persona aprueba o rechaza) -> END
                         +-- END (faltan presupuesto o uso: se pregunta al usuario)
```

- `supervisor`: elige el siguiente rol con el LLM; si la elección no vale, decide una regla en Python. Tiene un tope de vueltas (`MAX_ITER`).
- `requisitos`: traduce el pedido a requisitos técnicos y a un reparto del presupuesto. Suele usar el RAG, `describir_imagen` y `convertir_divisa`.
- `componentes`: elige piezas reales y comprueba la compatibilidad (socket, tipo de memoria, formato, fuente). Suele usar `buscar_componentes`, el RAG y `calcular_total_build`.
- `sintetizar`: junta las notas en un plan con viñetas; después Python suma los precios y los compara con el presupuesto.
- `aplicar`: solo se ejecuta tras la decisión humana. Pone `done=True` o vacía el plan guardando el motivo del rechazo.

La memoria entre turnos usa `MemorySaver` con `thread_id`. Hay más detalle en [`src/README_GRAFO.md`](src/README_GRAFO.md).

### Tools (allowlist en `src/tools/__init__.py`)

| Categoría | Tool | Qué hace |
|---|---|---|
| RAG completo | `RAG_consultar_catalogo` | `responder()` del PB1: respuesta basada en el corpus con sus fuentes, o abstención |
| Catálogo | `buscar_componentes` | Productos reales del CSV por categoría y rango de precio, con sus especificaciones |
| API externa | `convertir_divisa` | [Frankfurter](https://frankfurter.dev) (tipos del BCE, sin clave), con `data/divisas_fallback.json` si no hay red |
| Auxiliares | `calcular_total_build`, `hora_actual` | Suma de la configuración frente al presupuesto, y fecha y hora |
| Multimodal | `describir_imagen` | Gemini lee `assets/imagen_demo.jpg` (ficha técnica de prueba) u otra imagen de `assets/` |

Cada llamada queda en la traza con `tool`, `args`, `status` (`ok`, `error` o `blocked`) y `preview`. Las tools se pueden probar por separado, sin gastar API, con `python -m src.verificar_grafo`.

### Instalación y ejecución del agente

1. Sigue los pasos de [Entorno virtual](#entorno-virtual) (el `requirements.txt` ya incluye LangGraph) y crea el `.env` a partir de `.env.example`.
2. El índice del RAG está en el repositorio. Para regenerarlo: `python main.py --prepare` y `python main.py --index --recreate-index`.
3. Comprobaciones sin API:

   ```bash
   python -m src.verificar_grafo
   ```

4. CLI del agente:

   ```bash
   python -m src.cli                    # demo, con el HITL aprobado automáticamente
   python -m src.cli --sin-auto-aprobar # se queda en la pausa HITL
   python -m src.cli --interactivo      # chat; con un plan pendiente: aprobar / rechazar
   ```

5. Streamlit: `streamlit run app.py`.

### Cómo probar el HITL y la parte multimodal

- HITL: en `--interactivo` o en Streamlit, escribe "Ya tengo un Ryzen con socket AM4, ¿qué placa base y RAM me recomiendas por menos de 150 USD?". Cuando salga el plan, recházalo con el motivo "como mucho 120 USD", pide "Ajústalo a ese límite" y después apruébalo (`done=True`).
- Multimodal: "Mira la ficha técnica de la imagen y dime qué placa base y RAM compatibles me recomiendas por menos de 150 USD". En la traza aparece `describir_imagen`.
- Fuera de dominio: "¿Cuál es la capital de Francia?". El agente explica para qué sirve y no inventa.

Los límites los decide Python: `MAX_ITER` (supervisor), `max_steps` (tools por especialista) y `max_turns` (mensajes). Con la API gratuita de Gemini un turno tarda 2-3 minutos, porque espaciamos las llamadas para no recibir errores 429.

Todos los datos son públicos y de uso educativo, la imagen de prueba la hicimos para el proyecto y no hay claves en el repositorio (`.env` está en `.gitignore`).

## Tecnologías utilizadas

| Área | Tecnología | Uso en el proyecto |
|---|---|---|
| Lenguaje | **Python 3.10+** | Todo el pipeline y la interfaz |
| Carga de documentos | **LangChain** (`langchain-core`, `langchain-community`) | `Document`, `TextLoader`, `PyPDFLoader` |
| Chunking | **langchain-text-splitters** | `MarkdownHeaderTextSplitter` + `RecursiveCharacterTextSplitter` |
| Datos tabulares | **pandas** | Lectura y filtrado de los CSV del catálogo |
| PDF | **pypdf** | Extracción de texto de guías en PDF |
| Embeddings | **Google GenAI SDK** (`google-genai`) · modelo `gemini-embedding-001` | Vectorización de chunks y consultas (768 dimensiones) |
| Embeddings alternativos | **sentence-transformers** (opcional) | Embeddings locales sin API |
| Base vectorial | **ChromaDB** | Índice persistente con distancia coseno y metadatos |
| Generación | **Gemini** (`gemini-3-flash-preview`) | Redacción de la respuesta anclada al contexto |
| Agente | **LangGraph** + `langchain-google-genai` | Grafo multiagente, `MemorySaver`, `interrupt_before` (HITL), tools `@tool` |
| API externa | **Frankfurter** (BCE) | Conversión de moneda con fallback local |
| Interfaz | **Streamlit** | Chat del agente, botones HITL y depuración |
| Configuración | **python-dotenv** | Carga de la API key desde `.env` |
| Utilidades | **BeautifulSoup4** | Conversión de guías HTML a Markdown para ampliar el corpus |
| Control de versiones | **Git + GitHub** | Ramas `main` / `develop` / `feature/*` y pull requests |
## Desarrolladores del proyecto
 - Mario Bac Díaz (github: Ameisin)
 - Javier (github: TermiJP)
 - Jaime Pérez (github: JaimePVillanueva)

## Conclusión

PCompAgent cierra de punta a punta una arquitectura RAG completa: un corpus propio en dos formatos, un índice vectorial persistente en ChromaDB, retrieval *top-k* y generación con Gemini anclada exclusivamente al contexto recuperado. Todo ello con una separación clara entre el pipeline offline de indexación y el pipeline online de consulta, y con una API interna (`responder`) que la CLI y la interfaz Streamlit comparten sin duplicar lógica.

### Qué hemos aprendido

- **El corpus manda.** La mayor parte del esfuerzo no ha estado en el LLM sino en preparar los datos: convertir filas de CSV en frases con sentido, enriquecerlas con conocimiento derivado (socket, tipo de memoria, formatos de placa) y elegir una estrategia de chunking distinta para tablas y para guías. Un retrieval mediocre no se arregla con un prompt mejor.
- **Configuración centralizada y regenerable.** Tener `CHUNK_SIZE`, `TOP_K`, el modelo de embeddings y los filtros del corpus en `config.py`, junto con un índice que se reconstruye con un solo comando, ha permitido experimentar sin miedo a romper nada.
- **Abstenerse es una funcionalidad, no un fallo.** Un asistente que reconoce que la información no está en sus documentos es más útil y más fiable que uno que responde siempre.
- **Trabajo en equipo con Git.** Ramas por bloque funcional y pull requests revisadas han hecho que la integración del corpus, el retrieval, la generación y la interfaz haya sido incremental y trazable.

### Limitaciones actuales

- El asistente responde bien a preguntas sobre un componente, una compatibilidad o una guía concreta, pero no está diseñado para montar configuraciones completas por presupuesto: eso exige razonamiento sobre varios fragmentos y restricciones a la vez.
- Los precios y el catálogo son una foto fija del dataset y no reflejan el mercado actual.
- La evaluación es ligera y manual: mide retrieval con varios valores de K y revisa a ojo grounding y abstención sobre un conjunto reducido de preguntas.

---


