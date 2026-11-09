# Cómo armar una PC de gaming — Guía completa (Intel)

Fuente: Intel, "Cómo armar una PC de gaming - Guía completa".
URL: https://www.intel.la/content/www/xl/es/gaming/resources/how-to-build-a-gaming-pc.html
Consultada el 10/09/2026. Uso educativo (Project Break RAG).

Nota del equipo: este fichero es una versión curada de la guía (misma estructura de
secciones y pasos, texto resumido y con alguna aclaración añadida por el equipo sobre
compatibilidades). Para regenerar el texto íntegro tal cual aparece en la web ejecuta
`python scripts/descargar_guia_intel.py`, que sobrescribe este fichero.

## Preparación 1: Herramientas para armar una PC

Antes de comenzar conviene reunir las herramientas esenciales:

- Espacio de trabajo: una superficie amplia y despejada; evita trabajar sobre alfombra para
  reducir las descargas electrostáticas.
- Destornilladores: Phillips #2 para la mayoría de tornillos y Phillips #0 para los tornillos
  pequeños de las unidades M.2.
- Unidad flash USB de 8 GB o más para el instalador del sistema operativo.
- Sistema de organización: bandejas magnéticas o compartimentos para tornillos y piezas pequeñas.
- Iluminación: varias fuentes de luz, incluida una móvil (linterna o lámpara flexible).
- Muñequera antiestática: recomendada, aunque no obligatoria.
- Precintos (bridas) y tijeras para organizar los cables.

## Preparación 2: Gabinetes (cajas) de la PC de gaming

Los gabinetes o cajas vienen en tres tamaños principales:

- Torre completa (full tower): entre 55 y 61 cm de alto. Admite placas base Extended-ATX y
  ATX estándar. Es el formato con más espacio para refrigeración y ampliaciones.
- Torre intermedia (mid tower): entre 45 y 51 cm de alto. Es el tamaño más común e ideal para
  la mayoría de los armados; admite placas ATX, microATX y Mini-ITX.
- Minitorre y formatos compactos (SFF): pensados para placas Mini-ITX. Requieren una
  planificación exhaustiva de componentes (longitud de la GPU, altura del disipador, tamaño
  de la fuente) porque el espacio es muy limitado.

Considera dónde vas a ubicar la PC antes de elegir el tamaño. Los gabinetes más grandes
facilitan el trabajo durante el montaje y las futuras actualizaciones, y suelen ofrecer mejor
flujo de aire.

## Preparación 3: Piezas de la PC para gaming

Componentes necesarios para un PC de gaming:

- CPU (unidad central de procesamiento)
- GPU (unidad de procesamiento de gráficos / tarjeta gráfica)
- Placa base
- Memoria RAM
- Almacenamiento (SSD y/o HDD)
- Fuente de alimentación (PSU)
- Refrigeración del sistema
- Periféricos para gaming
- Sistema operativo

### Unidad central de procesamiento (CPU)

La CPU es el cerebro de la PC: ejecuta las instrucciones para que los programas funcionen.
Para gaming, Intel recomienda un procesador Intel Core con una frecuencia Turbo máxima
elevada y un número alto de núcleos y subprocesos. Una frecuencia Turbo alta mejora el
rendimiento de un solo subproceso (más FPS en juegos que dependen de un núcleo), mientras
que más núcleos y subprocesos permiten multitarea (jugar y hacer streaming a la vez) y mejor
rendimiento en juegos optimizados para varios subprocesos. La CPU debe ser compatible con el
zócalo (socket) y el chipset de la placa base.

### Unidad de procesamiento de gráficos (GPU)

Las tarjetas gráficas independientes, como una GPU Intel Arc serie B, se conectan a la ranura
PCIe x16 de la placa base. Son el componente que más influye en los FPS del juego y permiten
técnicas avanzadas como el trazado de rayos (ray tracing) e Intel XeSS (escalado por IA).
Antes de elegir, revisa análisis de rendimiento (benchmarks) y los requisitos del sistema de
los juegos a los que quieras jugar, incluidos los futuros. Comprueba que la longitud de la
tarjeta cabe en el gabinete y que la fuente de alimentación tiene potencia y conectores
suficientes.

### Placa base

La placa base conecta todos los componentes entre sí. Se elige por tamaño (factor de forma) y
por compatibilidad:

- Extended ATX (E-ATX): 30,5 cm x 33 cm, hasta 8 ranuras de RAM.
- ATX: 30,5 cm x 24,4 cm, hasta 4 ranuras de RAM. Es el estándar más común.
- MicroATX: 24,4 cm x 24,4 cm, hasta 4 ranuras de RAM.
- Mini-ITX: 17 cm x 17 cm, generalmente 2 ranuras de RAM.

Asegúrate de que la placa sea compatible con tu CPU (mismo socket y chipset compatible) y ten
en cuenta futuras actualizaciones. Algunos chipsets Intel serie 800 soportan memoria RAM DDR5,
PCIe 5.0 y Wi-Fi 6E. El tamaño de la placa determina qué gabinetes puedes usar.

### Memoria (RAM)

Para gaming, desde 2022 se necesitan como mínimo 16 GB de RAM. Si planeas hacer streaming o
creación de contenido, considera 32 GB o más. La velocidad de la memoria debe coincidir con lo
que soportan la placa base y la CPU (consulta las especificaciones de ambas). Se recomienda RAM
compatible con Intel Extreme Memory Profile (Intel XMP) para activar velocidades optimizadas
con un solo ajuste en la BIOS. Instala los módulos en parejas (dual channel) para mejor
rendimiento.

### Almacenamiento

Hay dos tipos principales de almacenamiento:

- SSD (unidades de estado sólido): mucho más rápidas. Pueden usar interfaz SATA (más antigua y
  lenta) o NVMe sobre PCIe (mejor rendimiento). Factores de forma: 2,5 pulgadas (SATA) o M.2
  (SATA o NVMe).
- HDD (discos duros mecánicos): más económicos y con mayor capacidad por euro. Formatos de 2,5
  pulgadas (normalmente 5400 RPM) o 3,5 pulgadas (7200 RPM o más).

Muchos usuarios combinan un SSD NVMe para el sistema operativo y los juegos principales con un
HDD de gran capacidad para almacenamiento adicional.

### Fuente de alimentación (PSU)

La fuente debe ser potente y de buena calidad; una fuente barata puede dañar el resto de
componentes. Calcula la potencia necesaria sumando el consumo de CPU y GPU con margen (existen
calculadoras de vataje en línea). Tipos según el cableado:

- No modular: los cables vienen fijos; es la opción menos costosa.
- Semimodular: los cables esenciales (placa base y CPU) vienen fijos y el resto se conectan
  según necesidad; es la mejor opción para la mayoría.
- Totalmente modular: todos los cables son desmontables; máxima comodidad para la gestión de
  cables, pero más costosa.

Las certificaciones 80 PLUS (Bronze, Gold, Platinum, Titanium) indican la eficiencia energética.

### Refrigeración del sistema

- Refrigeración por aire: usa disipadores con ventiladores. Es la opción más económica y
  simple; su eficacia depende del flujo de aire del gabinete.
- Refrigeración por líquido: más eficiente para CPU de alto consumo, requiere más espacio.
  Puede ser todo-en-uno (AIO), que viene preensamblada y necesita un mínimo de mantenimiento,
  o de circuito personalizado, con mayor control pero instalación más compleja.

Todo sistema necesita un refrigerador de CPU dedicado; muchas CPU no incluyen disipador.

### Periféricos y sistema operativo

Monitores, teclados y ratones dependen de las preferencias personales. Conviene equilibrar los
componentes internos con periféricos de calidad (por ejemplo, un monitor con una tasa de
refresco acorde a los FPS que puede dar la GPU). Se recomienda Windows 11 para aprovechar las
últimas CPU y GPU de Intel.

## Paso 1: Instalar la CPU

1. Retira la placa base del embalaje antiestático y colócala sobre la caja de cartón.
2. Localiza el zócalo de la CPU, que viene con una tapa protectora.
3. Abre la bandeja del zócalo usando la palanca de metal.
4. Retira la CPU del embalaje sosteniéndola por los bordes, sin tocar los contactos.
5. Alinea las flechas o muescas de la CPU y del zócalo.
6. Coloca suavemente la CPU en el zócalo.
7. Baja la palanca de retención con presión moderada.

Consejo: la CPU solo encaja de una forma y no requiere fuerza. Si no entra, no la fuerces:
revisa la alineación.

## Paso 2 (opcional): Instalar las SSD M.2

1. Localiza la ranura M.2 en la placa base (suele estar entre el zócalo de la CPU y la ranura PCIe x16).
2. Retira el tornillo pequeño de sujeción con el destornillador Phillips #0.
3. Desliza la SSD M.2 en la ranura con un ángulo de unos 35 grados hasta que asiente.
4. Presiona hacia abajo y vuelve a colocar el tornillo.

## Paso 3: Instalar la refrigeración de la CPU

1. Consulta el manual del disipador para las instrucciones específicas de tu socket.
2. Verifica si necesitas instalar una abrazadera o placa trasera de montaje.
3. Aplica pasta térmica si el disipador no la trae preaplicada (una gota pequeña, del tamaño
   de un guisante, en el centro de la CPU).
4. Coloca el disipador sobre la CPU.
5. Ajusta los tornillos en patrón cruzado (en diagonal) para repartir la presión de forma uniforme.

## Paso 4: Instalar la memoria (RAM)

1. Determina cuántas ranuras de RAM tiene tu placa base.
2. Consulta el manual para saber qué ranuras usar si no vas a ocuparlas todas (normalmente la 2 y la 4).
3. Alinea el módulo usando la muesca entre los contactos dorados.
4. Inserta el módulo presionando hasta que las pestañas laterales se fijen con un clic.

## Paso 5 (opcional): Prueba fuera de la carcasa

Puedes hacer una prueba rápida antes de instalar todo en el gabinete:

1. Instala la GPU en la placa base.
2. Conecta la fuente a la placa base (conectores de 8 pines de CPU y 24 pines).
3. Conecta la GPU a la fuente.
4. Enciende puenteando los pines del interruptor de encendido con un destornillador.
5. Verifica que luces y ventiladores funcionan.
6. Apaga y desconecta todo antes de continuar.

## Paso 6: Montar la fuente de alimentación

1. Desembala la fuente y sus cables.
2. Determina la orientación: el ventilador debe apuntar hacia la rejilla de ventilación del gabinete si es posible.
3. Sujétala con cuatro tornillos al gabinete.
4. Pasa los cables por las aberturas de gestión de cables del gabinete.

## Paso 7: Instalar la placa base

1. Coloca el protector de E/S (I/O shield) en el gabinete si no viene integrado en la placa.
2. Verifica que los cables pasen por el lugar correcto antes de fijar la placa.
3. Alinea la placa base con el protector de E/S y los separadores (standoffs).
4. Coloca primero el tornillo central.
5. Atornilla usando todos los orificios disponibles (típicamente 9 en una placa ATX).
6. Conecta la fuente: conector de CPU de 8 pines (arriba) y conector de 24 pines (lateral).

## Paso 8: Instalar la GPU

1. Localiza la ranura PCIe x16 (la más larga y más cercana a la CPU).
2. Retira las cubiertas de las ranuras de expansión traseras que ocupará la tarjeta.
3. Alinea la GPU y empújala suavemente en la ranura hasta oír un clic.
4. Sujétala con uno o dos tornillos a la parte posterior del gabinete.
5. Conecta los cables de alimentación auxiliar (6+2 pines o 12VHPWR) si la tarjeta los requiere.

## Paso 9: Instalar el almacenamiento

1. Inspecciona los compartimentos (bahías) del gabinete.
2. Bahías sin herramientas: abre la palanca, coloca la unidad y desliza de vuelta.
3. Bahías con abrazadera: desliza la unidad entre la abrazadera y el lateral y atornilla.
4. Conecta las unidades SATA a la placa base con cables SATA.
5. Conecta las unidades a la fuente de alimentación.

## Paso 10: Instalar el sistema operativo

1. Prepara un USB con el instalador del sistema operativo (Windows 11 recomendado).
2. Conecta el USB, el monitor, el ratón y el teclado.
3. Enciende la PC.
4. Pulsa la tecla indicada en pantalla para entrar en la BIOS/UEFI.
5. Verifica que todos los componentes (CPU, RAM, unidades) sean reconocidos.
6. Cambia el orden de arranque para que el USB sea el primero.
7. Reinicia y sigue las instrucciones del instalador.

## Próximos pasos

Una vez completado el montaje: explora las capacidades del nuevo sistema, actualiza los
controladores (drivers) de la GPU, considera el overclocking si instalaste una CPU
desbloqueada (serie K) y optimiza la configuración del sistema para el máximo rendimiento.
