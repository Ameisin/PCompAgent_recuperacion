# Grafo multiagente, HITL y persistencia (src/)

En esta carpeta está la orquestación del agente con LangGraph: un supervisor que reparte el trabajo entre dos especialistas, un nodo que sintetiza el plan y un nodo `aplicar` que solo se ejecuta después de que una persona apruebe o rechace el plan (human-in-the-loop). La memoria entre turnos se guarda con `MemorySaver` por `thread_id`.

El RAG del PB1 (`logic.responder`) no lo hemos tocado: el agente lo usa como una tool más.

```text
mensaje -> procesar_turno(estado, mensaje, thread_id)   (src/agent.py)
        -> grafo multiagente con MemorySaver             (src/graph.py)
        -> tools de la allowlist                         (src/tools/)
        -> pausa antes de aplicar -> la persona aprueba o rechaza
CLI (src/cli.py) y Streamlit (app.py) son clientes del mismo contrato
```

## El grafo

```text
START -> supervisor --+-- requisitos ---+
                      +-- componentes --+--> supervisor -> ...
                      +-- sintetizar ---+
                FINISH --+-- aplicar (pausa HITL) -> END
                         +-- END (faltan datos: se pregunta al usuario)
```

- **supervisor**: elige el siguiente rol con el LLM (temperatura 0). Si contesta algo que no vale, decidimos en Python con `_fallback_siguiente` y `_eleccion_valida`. Tiene un tope de vueltas (`MAX_ITER`).
- **requisitos**: primero sacamos en Python el presupuesto y el uso. Si faltan, se deja una pregunta para el usuario y el turno termina. Si no, el especialista traduce el pedido a requisitos técnicos y a un reparto del presupuesto. Puede usar tools.
- **componentes**: busca piezas reales del catálogo, una búsqueda por categoría, y comprueba la compatibilidad (socket, tipo de memoria, formato, fuente). Puede usar tools.
- **sintetizar**: junta las notas en una respuesta y un plan con viñetas. Después sumamos los precios en Python y avisamos si se pasa del presupuesto.
- **aplicar**: solo corre tras la decisión humana. Si se aprueba, `done=True`. Si se rechaza, se vacía el plan y el motivo queda guardado en el historial del hilo.

Separamos dos especialistas porque son dos tareas distintas: entender qué necesita el usuario y encontrar qué piezas reales lo cumplen. Cada uno tiene su prompt y usa las tools para cosas distintas.

Pusimos la pausa antes de `aplicar` porque el plan es una recomendación de compra con precios, así que ninguna configuración se da por cerrada sin que una persona la apruebe viendo la suma real.

## Ficheros

- `config_grafo.py`: modelo, límites (`MAX_ITER`, `MAX_STEPS_DEFAULT`, `MAX_TURNS_DEFAULT`), ritmo de llamadas y rutas de las tools.
- `llm.py`: crea el `ChatGoogleGenerativeAI` y el limitador de peticiones por minuto.
- `state.py`: estado que ven la CLI y Streamlit.
- `graph.py`: `EstadoGrafo`, nodos, router y `build_graph` (con `MemorySaver` e `interrupt_before`).
- `agent.py`: `procesar_turno`, `aprobar_plan`, `nuevo_thread_id`, `historial_checkpoints` y `run_demo`.
- `guardrails.py`: reglas en Python para preferencias, datos que faltan y suma del presupuesto.
- `registro_tools.py`: punto por el que el grafo obtiene las tools y su descripción para los prompts.
- `tools/`: allowlist, validación de argumentos y las 6 tools.
- `cli.py`: cliente de terminal.
- `verificar_grafo.py`: 14 comprobaciones sin llamar a la API (con un LLM simulado).

## Instalación y ejecución

Desde la raíz del proyecto, con el índice del RAG ya construido:

```bash
python -m pip install -r requirements.txt
```

La clave `GEMINI_API_KEY` se lee del mismo `.env` que usa el RAG.

Comprobaciones sin API (conviene lanzarlas antes que nada):

```bash
python -m src.verificar_grafo
```

Demo con el HITL aprobado automáticamente:

```bash
python -m src.cli
```

Demo que se queda en la pausa HITL (`pendiente_hitl=True`, `done=False`):

```bash
python -m src.cli --sin-auto-aprobar
```

Chat en la terminal. Con un plan pendiente se escribe `aprobar` o `rechazar` (al rechazar pide un motivo opcional):

```bash
python -m src.cli --interactivo
```

Demo con otro pedido:

```bash
python -m src.cli --mensaje "PC para oficina, presupuesto de 400 USD"
```

Límites más bajos y supervisor sin LLM, para gastar menos cuota:

```bash
python -m src.cli --max-steps 1 --supervisor-reglas
```

### Variables de entorno opcionales

- `AGENTE_GEMINI_MODEL` (por defecto `gemini-3.1-flash-lite`): modelo de los nodos del agente.
- `AGENTE_RAG_MODEL` (por defecto el del agente): modelo con el que genera la tool RAG. El del PB1, `gemini-3-flash-preview`, solo admite 20 peticiones al día en la capa gratuita.
- `AGENTE_LLM_RPM` (10): peticiones por minuto del modelo del agente. La tool RAG las comparte si usa el mismo modelo.
- `AGENTE_RAG_RPM` (4): peticiones por minuto de la tool RAG cuando usa otro modelo.
- `AGENTE_SUPERVISOR_LLM` (1): con `0` el supervisor enruta solo con reglas.

## Cómo lo usan los clientes

La interfaz no tiene lógica del grafo: solo llama a estas funciones y muestra el estado.

```python
from src.agent import aprobar_plan, historial_checkpoints, nuevo_thread_id, procesar_turno
from src.state import crear_estado

# Al empezar o con "Nueva conversación"
estado = crear_estado("")
thread_id = nuevo_thread_id()

# Cada mensaje del chat
estado = procesar_turno(estado, mensaje, thread_id, max_steps=4, max_turns=6)

# Botones de la barra lateral, solo si estado["pendiente_hitl"]
estado = aprobar_plan(thread_id, True, estado)
estado = aprobar_plan(thread_id, False, estado, comentario="motivo opcional")
```

Campos del estado que usa la interfaz: `respuesta`, `plan`, `resumen_presupuesto` (`total`, `presupuesto`, `dentro`), `pendiente_hitl` (bloquear el chat y enseñar los botones), `done`, `error`, `log`, `traza` (por turno, con `log` y `tools`) y `thread_id`. `historial_checkpoints(thread_id)` devuelve las fotos del hilo sin llamar al modelo.

`procesar_turno` ya rechaza mensajes nuevos si hay un plan pendiente o si la conversación terminó, así que la interfaz no tiene que repetir esas reglas.

## Tools

Están en `src/tools/__init__.py`, con el mismo esquema que en clase: lista `TOOLS` de funciones `@tool`, `validar_args` y `ejecutar_tool`, que bloquea cualquier nombre que no esté registrado.

- `RAG_consultar_catalogo`: llama a `responder()` del RAG del PB1.
- `buscar_componentes`: busca en los CSV por categoría y precio. Usa `buscar_precio` de `tools/tools.py`.
- `convertir_divisa`: API de Frankfurter con un JSON local de respaldo si no hay red.
- `calcular_total_build` y `hora_actual`: auxiliares. La primera usa `calculate_build_total` de `tools/tools.py`.
- `describir_imagen`: Gemini lee una imagen de `assets/`.

Los prompts de los especialistas listan las tools a partir de `TOOLS` (nombre y docstring), así que para añadir una basta con registrarla. En la traza, el `status` es `blocked` si la respuesta contiene "no está permitida", `error` si empieza por "Error" y `ok` en el resto.

## Límites (los decide Python)

- `MAX_ITER` (8): vueltas del supervisor por turno.
- `max_steps` (4): vueltas entre modelo y tools dentro de cada especialista.
- `max_turns` (6): mensajes del usuario por conversación.
- Allowlist: una tool no registrada sale como `blocked`.
- `done`: solo lo pone `aplicar` después de la aprobación.
- `faltan_datos`: sin presupuesto ni uso no se recomienda un equipo.

## Persistencia

- `MemorySaver` vive en memoria, dentro del grafo, que se compila una vez por proceso (`get_app`). Si se reinicia el proceso se pierden los hilos; el siguiente paso sería `SqliteSaver`.
- Con el mismo `thread_id` se sigue el mismo hilo. El campo `historial` acumula los mensajes y las decisiones HITL, así que un rechazo con motivo o un dato que faltaba se tiene en cuenta en el siguiente turno.
- Con otro `thread_id` la conversación empieza vacía.

## Pruebas

- `python -m src.verificar_grafo`: 14 de 14 comprobaciones correctas.
- Tool RAG con una pregunta del corpus (placas AM4 por menos de 100 USD): devuelve placas reales con precio y fuente.
- Tool RAG con una pregunta fuera del corpus (capital de Francia): responde que no tiene esa información.
- Flujo completo con la imagen: lee la ficha (socket AM4), busca placa y RAM, propone un plan de 115,98 USD para un límite de 150, lo rechazamos con el motivo "como mucho 120 USD", propone otro de 100,97 USD en el mismo hilo y al aprobarlo queda `done=True`. El detalle está en `entregables/informe_decisiones.md`.
- CLI interactiva con un pedido ambiguo: pide presupuesto y uso sin generar plan; al darle los datos propone uno.

## Limitaciones conocidas

- **Índice del RAG incompleto.** El índice de Chroma solo tiene CPU, placas base, RAM, cajas y videojuegos (3.902 fragmentos); faltan gráficas, fuentes, almacenamiento y las guías. Por eso los precios de las piezas los sacamos con `buscar_componentes` desde los CSV. Para regenerarlo: `python main.py --prepare` y `python main.py --index --recreate-index`.
- **Cuota gratuita.** Un turno hace entre 10 y 20 peticiones y tarda de 2 a 4 minutos, porque el limitador las espacia para no recibir errores 429. Con `--supervisor-reglas` se ahorran unas 4. Si se agota el límite diario no se reintenta: la tool devuelve el error y sale en la traza.
- **Compatibilidad.** No hay una comprobación estructurada en Python. En una prueba salió RAM DDR5 para una placa AM4 (el plan lo avisaba, pero no lo impidió).
- **Preferencias por palabras clave.** Si un pedido está redactado de forma muy distinta puede no detectarse; en ese caso el agente pregunta en lugar de inventar.
