# Reflexión — generación RAG 

## 1. Caso in-corpus

- Pregunta: ¿Qué mide la magnitud 83?
- ¿La respuesta se apoya en el contexto? Sí: el FAQ indica que 83 = Temperatura (°C).
- Fuentes mostradas: típ. `faq_calidad_aire.md`

## 2. Caso fuera de corpus (abstención)

- Pregunta: ¿Cuál es la capital de Francia?
- ¿Se abstuvo o inventó? Con prompt restrictivo suele indicar que el contexto no aporta esa info.
- Si inventó: reforzar “solo contexto” y pedir abstención explícita.

## 3. Un ajuste que probaste

- Cambio: `TOP_K` de 1 a 3.
- Efecto: más contexto; a veces más ruido, pero mejor cobertura en preguntas ambiguas.

## 4. Conclusión

La generación cierra el RAG: el retrieval solo selecciona evidencia; el prompt y el LLM redactan. La UI debe reutilizar `responder()` sin duplicar el pipeline. Evaluar abstención evita alucinaciones en preguntas fuera de corpus.
