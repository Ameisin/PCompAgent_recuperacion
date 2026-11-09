# Informe de decisiones - Project Break 2: agente multiagente PCompAgent

Nuestro agente es un asesor de compra de PC construido sobre el RAG del PB1. A partir del uso y el presupuesto propone piezas reales del catálogo, comprueba compatibilidad y precio, y no cierra el plan hasta que una persona lo aprueba.

Las pruebas que citamos están hechas con Gemini (capa gratuita, modelo `gemini-3.1-flash-lite` para el agente), con un `thread_id` por conversación.

## 1. Grafo: por qué estos especialistas y este momento HITL

```text
START -> supervisor --+-- requisitos ---+
                      +-- componentes --+--> supervisor -> ...
                      +-- sintetizar ---+
                FINISH --+-- aplicar (pausa HITL) -> END
                         +-- END (faltan presupuesto o uso)
```

El RAG del PB1 respondía bien a preguntas sueltas, pero no sabía montar un equipo completo, porque eso necesita dos tipos de razonamiento distintos. Por eso usamos dos especialistas:

- `requisitos` se encarga de entender qué necesita el usuario: uso, rendimiento, requisitos de un juego y reparto del presupuesto. Si hace falta, lee la ficha de la imagen o convierte la moneda.
- `componentes` busca qué piezas reales cumplen esos requisitos y si son compatibles entre sí (socket, tipo de memoria, formato de placa y caja, fuente).

`sintetizar` junta las notas de los dos en un plan con viñetas, y antes de la pausa sumamos los precios en Python y los comparamos con el presupuesto.

El supervisor elige el siguiente paso con el LLM, pero comprobamos en Python que la elección tenga sentido: si la palabra no es un rol válido, si se salta un paso o si repite uno que ya está hecho, decide la regla de respaldo. `MAX_ITER` evita bucles. Si faltan presupuesto y uso, el turno termina con una pregunta y no hay HITL, porque no hay ningún plan real que aprobar.

Pusimos la pausa antes de `aplicar` porque el plan es una recomendación de compra con dinero de por medio. El modelo propone, la persona aprueba o rechaza (con un motivo si quiere) viendo la suma real, y es Python quien pone `done`. Lo implementamos con `interrupt_before=["aplicar"]` y `MemorySaver`, y se reanuda con `update_state` e `invoke(None)` en el mismo `thread_id`.

## 2. Tools: qué hace cada una y cómo se conecta el RAG

La allowlist está en `src/tools/__init__.py`. El LLM propone la llamada, `ejecutar_tool` valida los argumentos y bloquea cualquier tool que no esté registrada. Cada llamada queda en la traza con `tool`, `args`, `status` y `preview`.

| Categoría | Tool | Qué hace |
|---|---|---|
| RAG completo | `RAG_consultar_catalogo` | Llama a `logic.responder()` del PB1 (ChromaDB, embeddings de Gemini, respuesta basada en el contexto y abstención) |
| Catálogo | `buscar_componentes` | Productos reales del CSV por categoría y rango de precio, con sus especificaciones. Usa `tools/tools.py` |
| API externa | `convertir_divisa` | API de Frankfurter (tipos del BCE, sin clave). Si no hay red usa `data/divisas_fallback.json` y lo indica con `fuente: fallback` |
| Auxiliares | `calcular_total_build`, `hora_actual` | Suma de la configuración frente al presupuesto, y fecha y hora |
| Multimodal | `describir_imagen` | Gemini lee `assets/imagen_demo.jpg`; solo acepta imágenes de `assets/` |

El grafo no sabe nada del RAG: solo ve una tool cuyo docstring explica para qué sirve. La tool llama a `responder(consulta, top_k, modelo)`, que es la API interna del PB1, sin pasar por Streamlit y sin cambiar nada del RAG.

Probamos cada tool por separado, fuera del grafo:

- RAG con una pregunta del corpus ("¿Qué tipo de memoria usa una placa base con socket AM4?"): responde que usan DDR4 y cita `motherboard.csv`.
- RAG con una pregunta fuera del corpus ("¿Cuál es la capital de Francia?"): dice que el contexto no tiene esa información.
- API: `700 EUR = 783.51 USD (fecha: 2026-10-23, fuente: api)`. Sin red, el verificador comprueba que responde con el respaldo local.
- Allowlist: una tool inventada devuelve "Error: tool ... no está permitida" y sale como `blocked` en la traza. `python -m src.verificar_grafo` pasa las 14 comprobaciones.

## 3. HITL: una aprobación y un rechazo

Todo en el mismo hilo, con el pedido "Mira la ficha técnica de la imagen y dime qué placa base y RAM compatibles me recomiendas por menos de 150 USD".

**Turno 1 (215 s).** El log muestra supervisor, requisitos, componentes, sintetizar y FINISH. Se usaron `describir_imagen` (Ryzen 5 5600, socket AM4), `buscar_componentes` (placas de 70 a 100 USD y RAM de 40 a 60 USD) y `calcular_total_build`. El plan fue:

- Placa base: ASRock B450M/ac R2.0, 74,99 USD
- RAM: Patriot Viper 4 Blackout 16 GB (2x8 GB, DDR4-3600), 40,99 USD

En total 115,98 USD, dentro de los 150. El grafo se quedó en pausa antes de `aplicar` y el chat se bloqueó.

**Rechazo con el motivo "Como mucho 120 USD".** `aplicar` se ejecuta igualmente, ve que el plan no está aprobado, lo vacía y guarda el motivo en el historial del hilo.

**Turno 2 (114 s), "Ajústalo a ese límite".** Gracias al checkpointer, el nuevo turno conoce el pedido anterior y el motivo, y el presupuesto pasa a 120 USD. El nuevo plan:

- ASRock B450M-HDV R4.0, 69,98 USD
- Timetec PINNACLE Konduit 16 GB (1x16 GB, DDR4-3200), 30,99 USD

En total 100,97 USD.

**Aprobación.** `aplicar` cierra con `done=True` y el historial de checkpoints muestra la pausa y el cierre.

Comprobamos en los CSV que todos los productos y precios existen, y que son compatibles: placas AM4 con memoria DDR4. También vimos que el rechazo con motivo sí cambia el resultado, porque el motivo entra en las preferencias del siguiente turno.

## 4. Multimodal

Usamos `assets/imagen_demo.jpg`, una ficha técnica de demostración que hicimos para el proyecto: AMD Ryzen 5 5600, socket AM4, 6 núcleos y 12 hilos, 3,5/4,4 GHz, 65 W, DDR4-3200 en dual channel y 129,99 USD.

Probada por separado, la tool devolvió todas las especificaciones correctas y además indicó que la imagen es de demostración.

Dentro del grafo, el especialista `requisitos` la usó para sacar el socket y el tipo de memoria, y con eso `componentes` filtró placas AM4 y RAM DDR4. Es decir, la imagen cambia de verdad el plan.

## 5. Tres fallos y qué haríamos en la siguiente fase (MLOps)

1. **Integración tardía de las partes.** Cada uno trabajó en su rama y no juntamos todo hasta el final. Al hacerlo, el Streamlit se había mergeado a `main` sin pasar por `develop` y llamaba a funciones que no existían, y las tools no seguían el formato que esperaba el grafo (otro proveedor de LLM, columnas de CSV con otros nombres). Para la siguiente fase pondríamos un CI en cada PR que ejecute `python -m src.verificar_grafo` y arranque `app.py` con `streamlit.testing`, y acordaríamos por escrito el formato de las tools antes de programarlas.
2. **Índice vectorial incompleto.** El índice solo tiene CPU, placas base, RAM, cajas y videojuegos; faltan gráficas, fuentes, almacenamiento y las guías. Cuando solo usábamos el RAG, esas piezas salían como "sin dato en el catálogo". Lo resolvimos con `buscar_componentes` sobre los CSV. El siguiente paso sería un proceso de indexado reproducible que compruebe que están todas las categorías, y no guardar el índice (unos 70 MB) en el repositorio sino generarlo al desplegar.
3. **Cuota y tiempo de respuesta.** Con la API gratuita, `gemini-3-flash` admite 5 peticiones por minuto y 20 al día, y llegamos al límite diario durante las pruebas. Un turno tarda entre 2 y 4 minutos porque espaciamos las llamadas para no recibir errores 429. Lo mitigamos usando `gemini-3.1-flash-lite` para el agente y el RAG, con un limitador por modelo y un reintento que respeta la espera que pide el servidor. En producción mediríamos coste y tiempo por turno (LangSmith u OpenTelemetry), guardaríamos en caché las consultas repetidas al RAG y usaríamos un modelo de pago.

Otros límites que hemos visto:

- No comprobamos la compatibilidad de forma estructurada en Python. En una prueba anterior salió RAM DDR5 para una placa AM4 (el plan lo avisaba, pero no lo evitó), y en el turno 2 de arriba eligió un solo módulo de 16 GB aunque la ficha recomienda dual channel. Una tool de compatibilidad que use los campos de socket y tipo de memoria del CSV lo resolvería.
- `MemorySaver` vive en memoria, así que la pausa HITL se pierde si se reinicia el proceso. El siguiente paso es `SqliteSaver` o Postgres.
- `tools/agent_rag_tools.py` es un prototipo inicial con otro proveedor de LLM y un agente ReAct propio. No está conectado al agente final, que usa el RAG del PB1.
