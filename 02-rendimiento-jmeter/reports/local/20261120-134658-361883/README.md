# JMeter local con un hilo de inferencia

Corrida de referencia del 20 de noviembre de 2026 a las 13:46:58, hora de Lima. La API local en `http://127.0.0.1:8012` inició con 12 imágenes y 12 vectores.

Las 64 muestras cumplieron sus aserciones. Ambos perfiles quedaron en **REVISAR** por el p95. [Datos de la ejecución](ejecucion.json).

| Perfil | Estado | Muestras | Fallos | Hilos máximos | Muestras/s | Archivos |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| pico | REVISAR | 42 | 0 | 8 | 1,641 | [JTL](pico/muestras.jtl) · [Métricas](pico/metricas.json) |
| escritura | REVISAR | 22 | 0 | 2 | 0,821 | [JTL](escritura/muestras.jtl) · [Métricas](escritura/metricas.json) |

**pico**

- Búsqueda por texto `BUS-01` con p95 de 12,456 s frente a un objetivo de 8,500 s.
- Búsqueda por imagen `BUS-02` con p95 de 11,315 s frente a un objetivo de 11,000 s.

**escritura**

- Subida `ESC-01` con p95 de 11,714 s frente a un objetivo de 10,000 s.
