# Registrar las pruebas de VisionText en Jira

## Qué registrar

Crea una tarea por suite en el proyecto de Jira y una subtarea por caso o perfil. Si el proyecto ya usa un tipo de incidencia para pruebas, usa ese tipo y vincúlalo con la tarea de la suite. Conserva el ID que aparece en el código y en el resultado para que se puedan buscar juntos.

| Suite | Casos que se registran | Código y evidencia |
| --- | --- | --- |
| Karate | 52 casos. Usa los IDs `SRV`, `TXT`, `IMG`, `CAT`, `APK`, `AUTH`, `ADM`, `UPL`, `CIC` y `RATE` de los escenarios. | [Escenarios](../01-api-karate/features/) · [JUnit por caso y entorno](../01-api-karate/reports/README.md) |
| JMeter | 10 perfiles. `inicio`, `rutas`, `base`, `carga`, `admin` y `web` tienen resultado en ambos entornos. `incremental`, `pico`, `sostenida` y `escritura` son locales. | [Planes JMX](../02-rendimiento-jmeter/plans/) · [JTL y métricas](../02-rendimiento-jmeter/reports/README.md) |
| Selenium | `WEB-01` a `WEB-08` en ambos entornos y `WEB-09` a `WEB-11` solo en local. | [Casos](../03-web-selenium/README.md#casos-de-la-suite) · [JUnit y capturas](../03-web-selenium/reports/README.md) |
| Appium | `APP-01` a `APP-09` en ambos entornos y `APP-10` a `APP-11` solo en local. | [Casos](../04-movil-appium/README.md#casos) · [JUnit, versión de APK y capturas](../04-movil-appium/README.md#resultados) |

## Cargar cada caso

1. Crea la incidencia con el ID al inicio del resumen, por ejemplo `[WEB-10] Subir y eliminar una imagen temporal`. Asigna un responsable y usa la etiqueta `visiontext-qa` junto a la de la herramienta.
2. En la descripción indica el requisito que verifica, los datos de prueba, los pasos y el resultado esperado. Agrega el enlace al archivo del caso y usa **Agregar → Incidencia vinculada** para relacionarlo con el requisito existente.
3. Registra una fila por entorno ejecutado con la fecha, la versión del sistema, el resultado real y la evidencia. Si el caso se repite, agrega una fila o un comentario nuevo con su fecha. Para un entorno fuera del alcance escribe `No aplica`. Si se interrumpió por conexión, registra `Bloqueado` y adjunta la captura disponible.
4. Agrega el enlace a GitHub en la descripción o mediante **Agregar → Enlace web**. Usa un enlace con el SHA del commit y la ruta del archivo, por ejemplo `https://github.com/Edithson1/calidad-pruebas/blob/<commit>/<ruta>`. Para adjuntar una captura, arrástrala a la incidencia o usa **Agregar → Adjunto**. El XML y el JTL pueden quedar enlazados desde GitHub. [Enlaces y adjuntos en Jira Cloud](https://support.atlassian.com/jira-software-cloud/docs/add-files-images-and-other-content-to-describe-an-issue/).
5. Para JMeter, registra también cuántas muestras se tomaron, el p95 observado y su objetivo. Si lo supera, registra `REVISAR` aunque todas las muestras hayan cumplido sus aserciones. Vincula el problema de rendimiento a la prueba y conserva los resultados anteriores cuando vuelvas a medir.

## Plantilla de la incidencia

```text
Resumen: [ID] Qué comprueba
Requisito: clave de Jira y criterio que cubre
Archivo de prueba: enlace al .feature, .jmx o .py en GitHub
Datos y preparación: catálogo, archivo de entrada y versión de VisionText
Pasos: 1. …  2. …  3. …
Resultado esperado: salida, código HTTP o umbral

Ejecuciones
Fecha y hora | Entorno, versión y URL | Resultado real | Estado | Evidencia
             | Local                  |                |        |
             | Desplegado             |                |        |
```

## Ejemplos con los resultados guardados

- **`WEB-10` · Subir y eliminar una imagen.** Desde la web local, inicia sesión con la cuenta temporal, sube un JPEG con descripción, localiza el alta en Admin, cancela el primer borrado y luego confírmalo. El 19 de noviembre la subida y el borrado pasaron. El catálogo volvió a 32 registros, 32 vectores, 32 originales y 32 miniaturas. La ejecución desplegada queda como `No aplica`. [Caso Selenium](../03-web-selenium/tests/test_visiontext.py) · [JUnit y capturas](../03-web-selenium/reports/README.md).
- **`pico` · Búsqueda con hasta 8 usuarios virtuales.** En local se esperaban p95 de hasta 8,5 s en texto y 11 s en imagen. Registra `REVISAR` para la corrida del 18 de noviembre y la repetición del 20 con un hilo. Agrega una ejecución `APROBADO` para el 20 de noviembre con cuatro hilos. Sus p95 fueron 6,075 s y 5,583 s en 42 muestras válidas. Incluye la configuración de cada corrida en Jira. [Plan del perfil](../02-rendimiento-jmeter/plans/local/pico.jmx) · [Historial de las mediciones](../02-rendimiento-jmeter/reports/README.md#seguimiento-local-del-20-de-noviembre) · [Muestras JTL de la corrida aprobada](../02-rendimiento-jmeter/reports/local/20261120-134958-050032/pico/muestras.jtl).

En la tarea de cada suite deja el total por entorno, el enlace al índice de resultados y las claves reales de los hallazgos. Antes de cerrar la revisión comprueba que desde Jira se pueda llegar al requisito, al caso y a su evidencia. [Resultados de las cuatro suites](../README.md).
