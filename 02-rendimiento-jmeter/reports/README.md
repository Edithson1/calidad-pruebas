# Resultados de JMeter para VisionText

Ejecuciones del **18 de noviembre de 2026**, hora de Lima. Cada índice enlaza las muestras JTL y las métricas de su entorno. Puedes [reconstruir los dashboards de JMeter](../README.md#evidencia-y-lectura) con los JTL guardados.

| Entorno | Servicio medido | Resultado | Evidencia |
| --- | --- | --- | --- |
| Local | API en loopback, 12 imágenes, PostgreSQL, RustFS, CLIP ONNX y FAISS. Web compilada y servida en el equipo. | 345 muestras válidas, 8 de 10 perfiles dentro de sus objetivos. | [Reportes locales](local/20261118-150033-623716/README.md) |
| Desplegado | API en Render con 1575 imágenes y Google Drive. Web en Vercel. | 69 muestras válidas, 6 de 6 perfiles dentro de sus objetivos. | [Reportes de Render y Vercel](render/20261118-145555-743104/README.md) |

## Comparación con los mismos flujos

| Perfil y métrica | Local | Desplegado |
| --- | ---: | ---: |
| Base con 1 VU, p95 de búsqueda por texto | 1,20 s | 4,63 s |
| Base con 1 VU, p95 de búsqueda por imagen | 2,38 s | 5,87 s |
| Carga con 2 VU, p95 de búsqueda por texto | 3,47 s | 10,33 s |
| Carga con 2 VU, p95 de búsqueda por imagen | 2,43 s | 6,99 s |
| Carga con 2 VU, muestras/s totales | 1,072 | 0,450 |

La carga de dos VU registró **20 peticiones por entorno**, con cuatro búsquedas de cada tipo y sus descargas asociadas. Los catálogos, la red y el almacenamiento difieren. La comparación describe estas ejecuciones y el tamaño reducido de la muestra limita la interpretación de sus percentiles.

El primer acceso a Render tomó **54,74 s** y quedó registrado aparte. El proceso local estuvo listo en **11,96 s**. Su primera petición medida por JMeter, después de verificar salud, tomó **84 ms**. [Métrica del primer acceso a Render](render/20261118-145555-743104/inicio/metricas.json).

## Hallazgos de rendimiento local

El perfil `pico` llegó a **8 usuarios virtuales** y tuvo **42 respuestas que cumplieron sus aserciones individuales**. Quedó en **REVISAR** porque el p95 de búsqueda textual fue **11,29 s** frente a un objetivo de **8,5 s**, y el de búsqueda por imagen fue **12,75 s** frente a **11 s**. Las descargas de imágenes se mantuvieron en **23 ms o menos**. [Métricas de pico](local/20261118-150033-623716/pico/metricas.json).

En la rampa de seis usuarios, los p95 de texto e imagen fueron **7,46 s** y **8,14 s**. [Métricas de la rampa](local/20261118-150033-623716/incremental/metricas.json).

El perfil `escritura` completó las cuatro subidas y borrados. El p95 de subida fue **11,20 s** frente al objetivo de **10 s**. Al terminar, PostgreSQL y FAISS volvieron a **12** registros y RustFS a **12** originales y **12** miniaturas. [Métricas de escritura](local/20261118-150033-623716/escritura/metricas.json).

La prueba sostenida registró **132 muestras válidas** con hasta **3 usuarios**, en **74,10 s** entre la primera y la última muestra. [Métricas del perfil sostenido](local/20261118-150033-623716/sostenida/metricas.json).

[Guía y comandos de JMeter](../README.md).
