Fuente: Intel, página original en Guía de compra de placas base para videojuegos_ Intel.html
Fecha de descarga: 12/09/2026 (guardada manualmente desde el navegador). Uso educativo (Project Break RAG).
Texto extraído automáticamente con scripts/convertir_html_a_markdown.py.

# Cómo elegir una placa base para gaming

- Descripción general
- Zócalo del procesador
- Chipset
- Ranuras de expansión
- RAM
- Formato
- BIOS
- Conectores internos
- Puertos externos
- PCB
- Más información

## Información destacada:

- ¿De qué se compone una placa base?
¿De qué se compone una placa base?

- Chipset
Chipset

- Formato
Formato

- E/S
E/S

- Cómo se hacen las placas base
Cómo se hacen las placas base

Por

Las placas base son complejas. Vamos a examinarlas detenidamente, componente por componente, y a explicar cómo funcionan. 1 2

Las placas base son complejas. Vamos a examinarlas detenidamente, componente por componente, y a explicar cómo funcionan. 1 2

Escoger una placa base para videojuegos es sin duda uno de los factores más importantes a la hora de montar un ordenador.

¿Qué hace una placa base? Es la placa de circuitos que conecta todo el hardware al procesador, distribuye la electricidad desde la fuente de alimentación y define los tipos de dispositivos de almacenamiento, los módulos de memoria y las tarjetas gráficas (entre otras tarjetas de expansión) que pueden conectarse a tu computadora.

A continuación, analizaremos en detalle la anatomía de una placa base y te daremos toda la información que necesitas para aprender a elegir una placa base para tu computadora.

## Anatomía de una placa base

Una placa base es la placa de circuitos principal de una computadora. Aunque la estética de las placas base cambia con el tiempo, su diseño básico permite que sea más fácil conectar tarjetas de expansión, unidades de disco duro y módulos de memoria nuevos, además de reemplazar las piezas antiguas.

Veamos algunos de los términos que encontrarás cuando compares placas base.

## Zócalo del procesador

Las placas base suelen contener al menos un zócalo de procesador, lo que permite que tu CPU (el “cerebro” mecánico de la computadora) se comunique con otros componentes críticos. Estos incluyen la memoria (RAM), el almacenamiento y otros dispositivos instalados en las ranuras de expansión: es decir, dispositivos internos como las GPU y dispositivos externos como los periféricos.

(Sin embargo, no todas las placas base tienen un zócalo: en sistemas con menos espacio, como las mini PCs y la mayoría de las laptops, la CPU está soldada a la placa base).

Cuando elijas una placa base, comprueba la documentación de la CPU para garantizar que la placa sea compatible con la CPU. Los zócalos varían con el fin de admitir diferentes productos según su generación, desempeño y otros factores mediante el cambio del arreglo de pines. (El nombre del zócalo proviene del arreglo de pines: por ejemplo, el zócalo LGA 1151, que es compatible con CPU de 9na Generación, tiene 1151 pines).

Las placas base modernas conectan las CPU directamente a la RAM, desde la cual obtienen instrucciones de diferentes programas. También se conectan a algunas ranuras de expansión que pueden contener componentes de desempeño crítico, como GPUs y unidades de almacenamiento. La controladora de memoria se encuentra en la CPU, pero muchos otros dispositivos se comunican con la CPU a través del chipset, el cual controla varias ranuras de expansión, conexiones SATA, puertos USB y las funciones de sonido y red.

Algunos pines conectan la CPU a la memoria a través de huellas (líneas de metal conductor) en la placa base, mientras que otros son grupos de pines de alimentación o en tierra. Si la computadora tiene problemas para arrancar o para reconocer la memoria instalada, esto podría deberse a un pin doblado que no está haciendo contacto con la CPU, entre otros posibles problemas .

Los pines pueden estar situados en la placa base o en el paquete de procesador, esto depende del tipo de zócalo. Los zócalos antiguos (como Socket 1 de Intel) a menudo eran matrices de rejilla de pines (PGA), en las cuales los pines situados en la CPU encajaban en las zonas conductoras del zócalo.

Los zócalos de matriz de contactos en rejilla (LGA) que se utilizan en muchos chipsets modernos básicamente funcionan de forma opuesta: los pines del zócalo se conectan a zonas conductoras en la CPU. LGA 1151 es un ejemplo de este tipo de zócalo.

Los zócalos de procesador actuales usan la instalación ZIF (fuerza de inserción cero). Esto significa que solo debes colocar el procesador en su lugar y fijarlo con un pestillo, sin aplicar presión extra que podría doblar los pines sacándolos de su sitio.

Esta innovación entró en uso con Socket 1 de Intel en 1989, el cual era compatible con la CPU 80486 (o 486). Aunque los primeros diseños de Socket 1 podían requerir hasta 100 libras de fuerza para insertar una CPU, dentro de la misma generación de CPU, los fabricantes pudieron desarrollar diseños sencillos que prácticamente no requerían fuerza ni herramientas para su instalación.

## Chipset

El chipset es un pilar de silicio integrado en la placa base, el cual funciona con determinadas generaciones de CPU. Retransmite la comunicación entre la CPU y los distintos dispositivos de almacenamiento y de expansión conectados.

Mientras que la CPU se conecta directamente a la RAM (a través de su controlador de memoria integrado) y a un número limitado de carriles PCIe* (ranuras de expansión), el chipset actúa como un concentrador que controla los otros buses en la placa base: carriles PCIe adicionales, dispositivos de almacenamiento, puertos externos, como ranuras USB, y muchos periféricos.

Los chipsets de gama superior pueden admitir más ranuras PCIe y puertos USB que los modelos estándar, además de configuraciones de hardware más recientes y asignaciones de ranuras PCIe diferentes (con más conexiones directas a la CPU).

El diseño clásico de chipset, habitual en los chipsets de la familia de procesadores Intel® Pentium®, se dividió en un “puente norte” y un “puente sur”, que manejaban distintas funciones de la placa base. Juntos, los dos chips formaron el “conjunto” de chips o chipset.

En este diseño antiguo, el puente norte, o el “concentrador de controladora de memoria”, estaba enlazado directamente a la CPU a través de una interfaz de alta velocidad llamada bus de sistema o bus frontal (FSB). Esto controlaba componentes críticos de desempeño del sistema: la memoria y el bus de expansión que se conectaba a una tarjeta gráfica. El puente sur, o el “concentrador de controladoras de E/S”, estaba conectado al puente norte con un bus interno más lento y controlaba prácticamente todo lo demás: otras ranuras de expansión, puertos Ethernet y USB, audio integrado y mucho más.

A partir de la 1ra Generación de procesadores Intel® Core™ en el 2008, en los chipsets Intel, se integraron las funciones del puente norte en la CPU. La controladora de memoria, uno de los principales factores que afectan el desempeño del chipset, está ahora dentro de la CPU, lo que reduce el retraso en las comunicaciones entre la CPU y la RAM. La CPU se conecta a un único chip (en lugar de dos): el concentrador de controladoras de plataforma (PCH), el cual controla carriles PCIe, funciones de E/S, Ethernet, el reloj de CPU y mucho más. Un bus de interfaz directa para medios (DMI) de alta velocidad crea una conexión de punto a punto entre la controladora de memoria de la CPU y el PCH.

## Cómo elegir un chipset

Los chipsets modernos consolidan muchas de las características que alguna vez fueron componentes discretos conectados a las placas base. El audio de placa, la wifi, la tecnología Bluetooth ® 3 , e incluso el firmware de cifrado ya se integran actualmente en los chipsets de Intel.

Los chipsets de gama alta, como el Z390, proporcionan numerosas ventajas, incluida la compatibilidad con overclocking y velocidades de bus más altas. Pero los chipsets Intel también proporcionan mejoras nuevas.

Aquí se muestra un desglose breve de las diferencias entre las series de chipsets Intel:

Serie Z

- Admite overlocking de CPU con designación “K”
- Un máximo de 24 carriles PCIe
- Hasta seis puertos USB 3.1 de 2da Generación
Serie H

- No admite overlocking
- Un máximo de 20 carriles PCIe
- Hasta cuatro puertos USB 3.1 de 2da Generación
Serie B

- No admite overlocking
- Un máximo de 20 carriles PCIe
- Solo puertos USB 3.0
Estas opciones diferentes permiten adquirirlo en una variedad de precios, a la vez que aprovechan las ventajas de los chipsets de la serie 300.

## Ranuras de expansión

PCIe

La interconexión de componentes periféricos exprés (PCIe) es un bus de expansión en serie de alta velocidad integrado en la CPU, el chipset de la placa base o ambos. Esto permite la instalación de dispositivos como tarjetas gráficas, unidades de estado sólido, adaptadores de red, tarjetas controladoras RAID, tarjetas de captura y otras muchas tarjetas de expansión en las ranuras PCIe de una placa base. Los periféricos integrados que se encuentran en muchas placas base también se conectan a través de PCIe.

Cada enlace de PCIe contiene una determinada cantidad de carriles de datos, enumerados como ×1, ×4, ×8 o ×16 (a menudo, se pronuncia “por uno”, “por cuatro”, etc.). Cada carril consta de dos pares de cables: uno que transmite información y otro que la recibe.

Con la generación actual de implementaciones de PCIe, un enlace de PCIe ×1 tiene un carril de datos con una velocidad de transferencia de un bit por ciclo. Un carril PCIe×16, típicamente la ranura más larga en la placa base (y también la más usada para una tarjeta gráfica), tiene 16 carriles de datos capaces de transferir hasta 16 bits por ciclo. Sin embargo, iteraciones futuras de PCIe permitirán duplicar la velocidad de datos por ciclo de reloj.

Cada versión de PCIe prácticamente duplicó el ancho de banda de la generación anterior, y eso significa un mejor desempeño para los dispositivos PCIe. Un enlace PCIe 2.0 ×16 tiene un ancho de banda bidireccional máximo teórico de 16 GB/s; un enlace PCIe 3.0 ×16 tiene un máximo de 32 GB/s. Cuando se comparan los carriles PCIe 3.0, el enlace ×4 que comúnmente se utiliza en muchas unidades de estado sólido tiene un ancho de banda máximo teórico de 8 GB/s, mientras que el enlace ×16 que se utiliza en las GPU ofrece cuatro veces más.

Otra característica de PCIe es la opción de utilizar ranuras con más carriles en lugar de ranuras con menor cantidad de carriles. Por ejemplo, una tarjeta de expansión ×4 se puede insertar en una ranura ×16 y funcionar normalmente. Sin embargo, su desempeño será el mismo que si estuviera en una ranura ×4, ya que los 12 carriles adicionales simplemente quedan sin utilizar.

Algunas placas base tienen ranuras PCIe y M.2 que podrían usar más carriles PCIe que los que están realmente disponibles en la plataforma. Por ejemplo, algunas placas base podrían tener siete ranuras PCIe x16, en las que teóricamente se podrían utilizar 112 carriles; sin embargo, el procesador y el chipset pueden tener solo 48 carriles.

Si todos los carriles están en uso, las ranuras PCIe a menudo cambiarán a una configuración de menor ancho de banda. Por ejemplo, si un par de GPU están instaladas en dos ranuras PCIe ×16, los enlaces pueden ejecutarse en ×8 en lugar de ×16 (es poco probable que se formen cuellos de botella en las GPU actuales por una conexión PCIe 3.0 ×8). Sin embargo, algunas placas base de primera categoría pueden utilizar conmutadores PCIe que se dispersan por los carriles físicos, de modo que las configuraciones de los carriles puedan permanecer sin cambios.

Las placas base para entusiastas, como las de la serie Z, proporcionan más carriles PCIe y una mayor flexibilidad para quienes arman computadoras.

M.2 y U.2

M.2 es un factor de forma compacto adecuado para dispositivos de expansión pequeños (de entre 16 mm y 110 mm de largo), como unidades de estado sólido NVMe (memoria exprés no volátil) y tarjetas Wi-Fi, entre otros.

Los dispositivos M.2 tienen diferentes “llaves” (la disposición de las conexiones doradas en el extremo) que determinan la compatibilidad con el zócalo en la placa base. Aunque pueden utilizar varias interfaces diferentes, las tarjetas M.2 más comunes utilizan cuatro carriles de datos de baja latencia PCIe o el bus SATA más antiguo.

Ya que las tarjetas M.2 son relativamente pequeñas, proporcionan una manera fácil de ampliar la capacidad de almacenamiento o la capacidad del sistema en un sistema más pequeño. Se conectan directamente a la placa base, lo cual elimina la necesidad de cables en los dispositivos tradicionales basados en SATA.

Los conectores U.2 son una interfaz alternativa que se conecta a las unidades SSD de 2,5" que utilizan conexiones PCIe por cable. Las unidades de almacenamiento U.2 se utilizan frecuentemente en entornos profesionales, como centros de datos y servidores, pero con menor frecuencia en computadoras armadas por consumidores.

U.2 y M.2 utilizan la misma cantidad de carriles PCIe y son capaces de alcanzar velocidades similares, aunque U.2 admite el intercambio en caliente (es decir, se puede extraer la unidad mientras el sistema sigue en uso) y puede admitir más configuraciones de energía que M.2.

SATA

SATA (Serial ATA) es un bus de computadora antiguo, de uso menos frecuente hoy en día, para conectar discos duros de 2,5" o 3,5", unidades de estado sólido y unidades ópticas que reproducen DVD y Blu-ray.

Aunque es más lento que PCIe, la interfaz SATA 3.0 común admite velocidades de transferencia de datos de hasta 6 Gbit/s. El nuevo formato SATA Exprés (o SATAe) utiliza dos carriles PCIe para alcanzar velocidades de hasta 16 GB/s. No debe confundirse con SATA externo (eSATA), el cual es un puerto externo que permite una fácil conexión de discos duros portátiles (compatibles).

Las ranuras de expansión han sido una característica esperada de las placas bases de computadoras desde el lanzamiento de la primera computadora personal de IBM en 1981, la cual utilizaba un bus de expansión de 16 bits llamado ISA (arquitectura estándar de la industria). Lo siguieron varios otros estándares de buses de expansión, como el bus local VESA PCI (interconexión de componentes periféricos), PCI-X y AGP (puerto de gráficos acelerado), una versión mejorada punto a punto del estándar PCI utilizado para conectar tarjetas gráficas al puente norte.

La diferencia clave entre PCIe y la tecnología PCI anterior es el uso de enlaces en serie, en lugar de enlaces en paralelo. Las transferencias de datos en paralelo de PCI significaban que el bus compartido estaba limitado a la velocidad del periférico más lento conectado al bus. PCIe proporciona conexiones punto a punto para cada dispositivo individual, y cada carril transfiere bits de forma secuencial.

## RAM

Las placas base también tienen ranuras para módulos RAM: módulos de memoria volátil que almacenan temporalmente los datos para una recuperación rápida. Múltiples módulos de alta velocidad de RAM pueden ayudar a las computadoras a manejar programas simultáneos sin desaceleración.

Las placas base de tamaño completo (como el formato ATX) normalmente tienen cuatro ranuras, mientras que las placas de tamaño limitado como las mITX suelen utilizar dos. Sin embargo, las placas base HEDT pueden tener hasta ocho.

Las placas base recientes admiten la arquitectura de memoria de doble canal, lo que significa que existen dos canales independientes que transfieren datos entre el controlador de memoria de la CPU y un módulo de RAM DIMM (módulos de memoria en línea doble). Mientras haya módulos de RAM instalados en pares con frecuencias que coincidan, esto tendrá como resultado una transferencia de datos más rápida y un mejor desempeño en algunas aplicaciones.

En chipsets anteriores, la CPU generalmente se comunicaba con la RAM en un proceso de varios pasos a través de su enlace con el puente norte/controlador de memoria mediante el bus frontal. En los chipsets Intel modernos, la controladora de memoria está integrada en la CPU y se accede a este mediante un enlace punto a punto de baja latencia denominado Intel® Ultra Path Interconnect (Intel® UPI).

## Formato

El formato de tu placa base determina el tamaño de torre que necesitas, la cantidad de ranuras de expansión con la que tendrás que trabajar y muchos aspectos del diseño y la refrigeración de la placa base. En general, los formatos más grandes brindan a los armadores de equipos una mayor cantidad de DIMM, PCIe de tamaño completo y ranuras M.2 con la que trabajar.

Para facilitar el proceso para los consumidores y los fabricantes, las dimensiones de la placa madre para computadora de escritorio están altamente estandarizadas. En cambio, los formatos de placa base para computadora portátil a menudo varían según el fabricante debido a las limitaciones únicas de tamaño. Esto también puede ocurrir en computadoras de escritorio prearmadas altamente especializadas.

A continuación, se muestran los formatos más comunes de placa base para computadora de escritorio:

- ATX (12” x 9,6"): El estándar actual para las placas base de tamaño completo. Una placa base ATX estándar para consumidor generalmente tiene siete ranuras de expansión, a una distancia de 1,78 cm (0,7 pulgadas) entre sí, y cuatro ranuras DIMM (de memoria).
- ATX extendido o eATX (12" x 13"): Una variante de mayor tamaño del formato ATX, diseñada para su uso por parte de profesionales y entusiastas; estas placas cuentan con espacio adicional para configuraciones de hardware más flexibles.
- Micro ATX (9,6" × 9,6"): Una variante más compacta de ATX, cuenta con dos ranuras de expansión (×16) de tamaño completo y cuatro ranuras DIMM. Encaja en minitorres, pero sigue siendo compatible con los orificios de montaje en las torres ATX de mayor tamaño.
- Mini-ITX (6,7" × 6,7"): formato pequeño diseñado para su uso en computadoras compactas sin enfriamiento de ventilador. Proporciona una ranura PCIe de tamaño completo y, por lo general, dos ranuras DIMM. Nuevamente, los agujeros de montaje son compatibles con las torres ATX.

## Todo lo que debes saber acerca del BIOS

Lo primero que ves cuando enciendes la computadora es el BIOS, o Sistema básico de Entrada/Salida. Este es el firmware que se carga antes de que el sistema operativo arranque, y se encarga de iniciar y probar todo el hardware conectado.

Aunque a menudo los usuarios y en las etiquetas de las placas base lo llaman BIOS, el firmware de las placas base modernas suele denominarse UEFI (Interfaz de firmware extensible unificada). Este entorno más flexible ofrece muchas mejoras fáciles de usar, como soporte para particiones de almacenamiento más grandes, un arranque más rápido y una moderna interfaz gráfica de usuario (GUI).

A menudo, los fabricantes de placas base agregan utilidades de UEFI que optimizan el proceso de overlocking de la CPU o la memoria de la computadora y proporcionan configuraciones prestablecidas útiles. También suelen tener una apariencia estilizada, agregan características de registro y captura de pantalla, simplifican procesos como el arranque desde otra unidad y muestran la memoria del monitor, la temperatura y la velocidad del ventilador.

Además, UEFI es compatible con antiguas características del BIOS. Los usuarios pueden arrancar en modo Heredado (también conocido como CSM o módulo de soporte de compatibilidad) para acceder al BIOS clásico, con lo cual se pueden resolver problemas de compatibilidad con programas o utilidades operativos anteriores. Sin embargo, cuando los usuarios arrancan en modo Heredado, obviamente pierden los beneficios modernos de UEFI, como el soporte para particiones con más de 2 TB. (Nota: Siempre respalde los datos importantes antes de cambiar de modo de arranque).

## Conectores internos

Para encender cada parte de la placa base, los cables de la fuente de alimentación y la torre deben estar enchufados a conectores y cabezales (pines expuestos) en la placa base. Consultar la referencia visual en el manual, así como el texto pequeño serigrafiado en la misma placa madre (como CPU_FAN), para conectar cada cable con el conector derecho.

Conectores de datos y alimentación

- Conector de alimentación de 24 pines
- Conector de alimentación de CPU de 12 V y 8 o 4 pines
- Conector de alimentación PCIe
- Conectores SATA Express/SATA 3
- Conectores M.2
Cabezales

- Cabezal del panel frontal: un grupo de pines individuales para las funciones del botón de encendido, el botón de restablecimiento, la luz LED del disco duro, la luz LED de alimentación, el altavoz interno y la torre
- Cabezal de sonido del panel frontal: alimenta los puertos para auriculares y altavoz
- Cabezales de bombeo y ventilador: para la refrigeración por agua de la CPU y el sistema
- Cabezales USB 2.0, 3.0 y 3.1
- Cabezal S/PDIF (audio digital)
- Cabezales de tira RGB

## Puertos externos

La placa madre es el concentrador al que se conectan los dispositivos externos, y su controladora de E/S administra estos dispositivos. Las placas base de consumidor proporcionan puertos que conectan la tarjeta gráfica integrada de una CPU al monitor (algo útil si no tienes una tarjeta de gráficos discreta o si buscas solucionar problemas de pantalla), periféricos como un teclado y mouse, dispositivos de audio, cables Ethernet y mucho más. Las diferentes versiones de estos puertos, como USB 3.1 Gen 2, pueden permitir mayores velocidades.

Las placas base agrupan los puertos externos en su panel posterior, el cual está cubierto con una “protección de E/S” extraíble o integrada. Esto está conectado a tierra debido a su contacto con una torre frecuentemente hecha de metal. A veces, esto está conectado a la placa base o viene por separado para su instalación cuando se arma el sistema.

Transferencia de datos y periféricos

- Puerto USB: un puerto de uso extendido que se utiliza para conectar mouse, teclados, auriculares, teléfonos inteligentes, cámaras y otros periféricos. Proporciona alimentación y datos (a velocidades de hasta 20 Gbit/s mediante USB 3.2). Las placas base actuales pueden incluir tanto el conector clásico USB tipo A y el conector tipo C más delgado y reversible.
- Puerto Thunderbolt™ 3 : un puerto de alta velocidad que utiliza un conector USB-C. La tecnología Thunderbolt™ 3 transfiere datos a velocidades de hasta 40 GB/s y también admite los estándares DisplayPort 1.2 y USB 3.1. El soporte para DisplayPort permite “conectar en cadena” varios monitores compatibles y manejarlos desde la misma computadora.
- Puerto PS/2: un puerto heredado, esta conexión de seis pines codificados por color se conecta a un teclado o mouse.
Pantalla

Estos puertos de pantalla se conectan a la solución de gráficos integrados de la placa base; una tarjeta gráfica instalada en una de las ranuras de expansión proporcionará sus propias opciones de puerto de pantalla.

- HDMI (Interfaz multimedia de alta definición): esta conexión digital de uso extendido admite resoluciones de hasta 8K a 30 Hz, al igual que la versión HDMI 2.1.
- DisplayPort: este estándar de pantalla admite resoluciones de hasta 8K a 60 Hz, al igual que DisplayPort 1.4. Aunque es más común en las tarjetas gráficas que en las placas base, muchas placas cuentan con soporte DisplayPort mediante su puerto Thunderbolt™ 3.
- DVI (Interfaz de video digital): un puerto heredado que data de 1999, esta conexión digital de 29 pines puede ser DVI de enlace simple o de enlace doble con mayor ancho de banda. La opción de enlace doble admite resoluciones de hasta 2560 x 1600 a 60 Hz. Se conecta fácilmente a VGA mediante un adaptador.
- VGA (Arreglo para gráficos de video): una conexión analógica de 15 pines con soporte para resoluciones de hasta 2048 x 1536 a una frecuencia de actualización de 85 Hz. Este puerto heredado aún se puede encontrar en las placas base. A menudo, sufre una degradación de señal con resoluciones más altas o cables más cortos.
Sonido

La parte frontal de la torre de una computadora suele tener dos puertos de audio analógicos de 3,5 mm etiquetados para auriculares (salida de auriculares) y un micrófono (entrada de micrófono).

El panel posterior de la placa base generalmente tiene un banco de seis puertos de audio analógicos de 3,5 mm codificados por colores y con etiquetas, utilizados para conectarse a sistemas de altavoces multicanal.

Los colores de los puertos de audio en tu placa base pueden variar según el fabricante; sin embargo, estos son los colores estándar:

Negro es la salida del altavoz posterior

Naranja es la salida del altavoz central/subwoofer

Rosa es la entrada de micrófono

Verde es la salida del altavoz frontal ( o los auriculares )

Azul es la entrada de línea

Plateado es la salida lateral de altavoz

Tu placa base puede también contar con conectores S/PDIF (Interfaz digital Sony/Philips), como un puerto de audio coaxial y óptico, que funciona con altavoces digitales, receptores de cine en casa, y otros dispositivos de audio. Esta opción puede ser útil si el dispositivo que está utilizando no admite transferencia de audio a través de HDMI.

Redes

La mayoría de las placas base de consumidor incluyen un puerto LAN RJ45, el cual puede conectarse al router o módem mediante un cable Ethernet. Algunas placas disponen de puertos dobles para utilizar con una antena Wi-Fi, así como funciones avanzadas de conectividad, como puertos dobles Ethernet de 10 Gigabit.

## ¿Qué es una PCB?

Es útil conocer algunos términos básicos relacionados con la fabricación de placas base, puesto que los manuales y los anuncios de fabricantes suelen hacer referencia a sus métodos de fabricación de PCB.

Una placa base moderna es una placa de circuito impreso (PCB) compuesta de capas de fibra de vidrio y cobre, con otros componentes montados encima o enchufados en ella.

Las PCB modernas suelen tener alrededor de 10 capas, lo cual hace que estén interconectadas a una densidad mucho mayor de lo que aparenta la superficie.

Cada “huella” conductora (las líneas visibles que cubren la superficie de la placa) es una conexión eléctrica independiente. Si una de estas huellas se daña, el circuito deja de estar completo y los componentes de la placa base dejarán de funcionar correctamente. Por ejemplo, si una huella que viene desde un enlace PCIe hasta la PCH recibe una ralladura profunda, es posible que la ranura PCIe ya no encienda la tarjeta de expansión instalada en ella.

Después de crear huellas conductoras mediante grabado químico, los fabricantes agregan la máscara de soldadura, una capa de polímero tradicionalmente verde que ayuda a prevenir la oxidación. También ayuda a prevenir daños por manipulación, a fin de garantizar que las huellas no se vean interrumpidas por un simple rasguño o golpe mientras instala la tarjeta madre en su torre.

## ¿Qué más elementos agregan los fabricantes?

Aunque los fabricantes de placas base no crean sus propios chipsets, tomas innumerables decisiones relacionadas con la fabricación, la estética y el diseño, así como a nivel de refrigeración, características del BIOS, el software Windows de la placa base y funciones de primer nivel. Aunque la gama de estas características es demasiado amplia para cubrirla en su totalidad, las adiciones más comunes caen en algunas categorías generales.

Overclocking

Las placas base de alta gama suelen proporcionar pruebas y ajustes automatizados para hacer overlocking a la CPU, la GPU y la memoria, lo cual proporciona una alternativa fácil de utilizar al ajuste manual de las cifras de frecuencia y voltaje en el entorno UEFI. También pueden tener un generador de reloj integrado para lograr un control preciso de la velocidad de la CPU, un módulo regulador de voltaje (VRM) avanzado, sensores térmicos extra cerca de componentes sobreacelerados e incluso botones físicos en la placa base para iniciar y detener el overlocking. Puedes aprender más sobre cómo hacer overlocking en tu computadora aquí .

Refrigeración

Los componentes de la placa base como el PCH y el VRM generan mucho calor. Para mantenerlos en temperaturas de funcionamiento seguras y evitar una limitación del desempeño, los fabricantes de placas base instalan una gama de soluciones de refrigeración. Estas van desde la refrigeración pasiva proporcionada por disipadores térmicos hasta soluciones activas como ventiladores pequeños o refrigeración integrada por agua.

Las soluciones de refrigeración activa tienen piezas movibles, como la bomba en un enfriador de agua o un ventilador giratorio. Las soluciones de refrigeración pasiva, como los disipadores térmicos, funcionan sin piezas móviles. A veces, se prefieren estas últimas opciones en condiciones hostiles, en las que las soluciones activas pueden tener una vida útil más corta, o cuando se prefiere una acústica más baja.

Software

Los paquetes de software de la placa base facilitan la administración de tu placa base dentro de Windows. Los conjuntos de funciones varían entre los fabricantes; sin embargo, el software puede realizar una búsqueda de controladores obsoletos, supervisar automáticamente las temperaturas, actualizar el BIOS de la placa base de forma segura, facilitar el ajuste de las velocidades de ventilador, ofrecer perfiles de ahorro de energía más detallados que en Windows* 10, o incluso rastrear el tráfico de red.

Sonido

Los códecs de audio avanzados, los amplificadores integrados, y los condensadores mejorados pueden mejorar el desempeño de los sistemas de audio incorporados. También se pueden separar los distintos canales de audio en diferentes capas de la PCB para evitar interferencias de señal.

Construcción

Muchos fabricantes anuncian técnicas de construcción de PCB que, según ellos, ayudan a aislar los circuitos de memoria y mejoran la integridad de la señal. Algunas placas base también cuentan con placas de acero adicionales encima de la PCB para proteger los conectores o brindar soporte a la tarjeta gráfica (normalmente, se fijan mediante un simple pestillo).

Iluminación RGB

Las placas base de alta gama suelen proporcionar cabezales RGB para alimentar un arreglo de luces LED con colores y efectos personalizables. Los cabezales RGB no direccionables alimentan tiras LED que muestran un solo color a la vez (con intensidades y efectos variables). Los cabezales RGB direccionables alimentan luces LED con múltiples canales de color, lo que les permite mostrar varios tonos a la vez. Normalmente, el software integrado y las aplicaciones de teléfonos ayudan a simplificar la configuración de las luces LED.

## Haz tu elección

Ya tengas previsto construir un nuevo PC o bien actualizar tu actual ordenador para videojuegos, conocer los componentes de tu placa base para juegos es fundamental. Una vez sepas qué hace cada cosa, sabrás cómo escoger una placa base para videojuegos que se adapte a tu creación.

Necesitas un zócalo que coincida con tu CPU, un chipset que maximice el potencial de tu hardware y, finalmente, un conjunto de características que satisfaga de mejor manera tus necesidades informáticas. Dedica un momento a enumerar varias placas base compatibles y compara sus ventajas clave antes de tomar una decisión; de esa forma, podrás encontrar exactamente lo que estás buscando.

### Resolución de problemas: la computadora no arranca Windows

### Preguntas frecuentes sobre computadoras: aclara tus dudas con los expertos en gaming de Intel

### Ve al núcleo de gaming

### Información sobre productos y desempeño

Las características y los beneficios de las tecnologías Intel® dependen de la configuración del sistema y podrían requerir hardware y software habilitados o la activación del servicio. El desempeño varía según la configuración del sistema. Ningún producto o componente puede proporcionar una seguridad absoluta. Consulte con el fabricante del sistema o el distribuidor minorista. O bien puede encontrar más información en https://www.intel.la.

Intel renuncia a toda garantía expresa o implícita, incluidas, entre otras, las garantías implícitas mercantiles, idoneidad para un propósito particular, y sin su contravención, así como cualquier otra garantía que surja de prestaciones, convenios u otro uso comercial.

La palabra Bluetooth® y sus logotipos son marcas registradas de Bluetooth SIG, Inc. y cualquier uso de estas marcas por parte de Intel Corporation se realiza bajo licencia.
