# VisionText en JMeter · local

Inicio de la ejecución `2026-11-18T15:00:33-05:00`.
API `http://127.0.0.1:8012`. Web `http://127.0.0.1:4173`.

Catálogo al medir `12` imágenes y `12` vectores. Almacenamiento `s3`. Inferencia `onnx`.

El proceso local tardó **11957 ms** en quedar listo. El perfil `inicio` mide la petición HTTP posterior a la comprobación de salud.

El catálogo y los conteos de RustFS volvieron a su estado inicial después de la escritura. [Datos de la ejecución](ejecucion.json).

| Perfil | Estado | Muestras | Fallos | Hilos máximos | Muestras/s | Archivos |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| inicio | APROBADO | 1 | 0 | 1 | 11.905 | [JTL](inicio/muestras.jtl) · [Métricas](inicio/metricas.json) |
| rutas | APROBADO | 11 | 0 | 1 | 4.45 | [JTL](rutas/muestras.jtl) · [Métricas](rutas/metricas.json) |
| base | APROBADO | 15 | 0 | 1 | 0.748 | [JTL](base/muestras.jtl) · [Métricas](base/metricas.json) |
| carga | APROBADO | 20 | 0 | 2 | 1.072 | [JTL](carga/muestras.jtl) · [Métricas](carga/metricas.json) |
| incremental | APROBADO | 64 | 0 | 6 | 1.67 | [JTL](incremental/muestras.jtl) · [Métricas](incremental/metricas.json) |
| pico | REVISAR | 42 | 0 | 8 | 1.616 | [JTL](pico/muestras.jtl) · [Métricas](pico/metricas.json) |
| sostenida | APROBADO | 132 | 0 | 3 | 1.781 | [JTL](sostenida/muestras.jtl) · [Métricas](sostenida/metricas.json) |
| admin | APROBADO | 20 | 0 | 2 | 3.65 | [JTL](admin/muestras.jtl) · [Métricas](admin/metricas.json) |
| escritura | REVISAR | 22 | 0 | 2 | 0.844 | [JTL](escritura/muestras.jtl) · [Métricas](escritura/metricas.json) |
| web | APROBADO | 18 | 0 | 2 | 3.938 | [JTL](web/muestras.jtl) · [Métricas](web/metricas.json) |

**pico**

- BUS-01: p95 de 11286.0 ms supera 8500 ms.
- BUS-02: p95 de 12752.0 ms supera 11000 ms.

**escritura**

- ESC-01: p95 de 11197.0 ms supera 10000 ms.
