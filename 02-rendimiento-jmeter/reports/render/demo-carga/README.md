# JMeter contra el sistema desplegado: repetición de demostración

Perfil `carga` de [`plans/render/carga.jmx`](../../../plans/render/carga.jmx), ejecutado desde la ventana de JMeter 5.6.3 contra la API en Render. Es una repetición aparte y no sustituye a la corrida publicada en [Resultados](../../README.md).

20 muestras y 0 fallos de aserción.

| Operación | Muestras | p95 | Objetivo p95 |
| --- | ---: | ---: | ---: |
| BUS-01 Búsqueda por texto | 4 | 9276 ms | 28000 ms |
| BUS-02 Búsqueda por imagen | 4 | 11406 ms | 32000 ms |

Con 4 muestras por operación, el p95 coincide con el valor máximo.

- [Muestras (JTL)](carga2.jtl)
- [Dashboard HTML (ZIP)](dashboard-html.zip): extraer y abrir `index.html`.

## Capturas del informe

Están en [`capturas-informe/`](../../capturas-informe/).

| Capturas | Contenido | Origen |
| --- | --- | --- |
| `fig4`, `fig8` | Aggregate Report y Summary Report | Primera repetición de `carga`; su JTL no se guardó, así que sus cifras difieren de las de arriba |
| `fig5a`, `fig5b` | Dashboard HTML | Generado desde `carga2.jtl` |
| `fig6`, `fig7a`, `fig7b` | Thread Group, CSV y aserción de duración | Plan `render/carga.jmx` |
| `fig9` | Dashboard de `pico` con un hilo de inferencia | JTL local ya publicado en `reports/local/20261120-134658-361883/pico/` |
