# JMeter local con cuatro hilos de inferencia

Corrida del 20 de noviembre de 2026 a las 13:49:58, hora de Lima. La API local en `http://127.0.0.1:8012` inició con 12 imágenes y 12 vectores.

Los dos perfiles cumplieron sus objetivos de p95 y aprobaron las 64 muestras. Después del perfil `escritura`, el catálogo, el índice y el almacenamiento recuperaron sus conteos iniciales. [Datos de la ejecución](ejecucion.json).

| Perfil | Estado | Muestras | Fallos | Hilos máximos | Muestras/s | Archivos |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| pico | APROBADO | 42 | 0 | 8 | 3,300 | [JTL](pico/muestras.jtl) · [Métricas](pico/metricas.json) |
| escritura | APROBADO | 22 | 0 | 2 | 1,473 | [JTL](escritura/muestras.jtl) · [Métricas](escritura/metricas.json) |
