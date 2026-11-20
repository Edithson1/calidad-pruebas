# Rendimiento de VisionText con Apache JMeter

Los planes de `plans/local/` y `plans/render/` se ejecutan con JMeter 5.6.3 y Java 21. Cada ejecución guarda su evidencia por entorno y perfil.

## Resultados

El 18 de noviembre de 2026, las 345 muestras locales y las 69 del despliegue cumplieron sus aserciones. En local quedaron en `REVISAR` los perfiles `pico` y `escritura` por superar sus objetivos de p95. En Render y Vercel se cumplieron los objetivos de los seis perfiles. [Comparación, JTL y métricas por perfil](reports/README.md).

## Ejecutar en Windows

Instala JMeter 5.6.3 y Java 21. El lanzador busca JMeter en Descargas y Java en Android Studio. Si los tienes en otra ubicación, pasa `-JMeterHome` y `-JavaHome`, o configura `JMETER_HOME` y `VT_JMETER_JAVA_HOME`. Usa el entorno de Python de `VisionText-backend/.venv/windows` con `requests` y `python-dotenv`. Los JPEG de [`consultas.csv`](data/consultas.csv) deben estar en `VisionText-backend/dataset_final/` para ambos entornos. Ejecuta desde `calidad/` en PowerShell. [Carpetas del proyecto](../README.md#carpetas-en-la-computadora).

### Desplegado

Si aún no tienes el entorno de Python del backend y solo vas a probar el despliegue, prepara el cliente con Python 3.12.

```powershell
py -3.12 -m venv .\VisionText-backend\.venv\windows
& .\VisionText-backend\.venv\windows\Scripts\python.exe -m pip install requests python-dotenv
```

```powershell
& '.\pruebas\02-rendimiento-jmeter\Ejecutar-JMeter.ps1' -Entorno render
```

Mide la API de Render y la web de Vercel. `admin` usa `VT_JMETER_ADMIN_USER` y `VT_JMETER_ADMIN_PASSWORD`, o la configuración privada `VisionText-backend/.env.render`. Este perfil hace un inicio de sesión, consulta el catálogo y comprueba el almacenamiento. Usa `-SoloPublico` si vas a medir solo los perfiles públicos. [Enlaces del despliegue](../README.md#enlaces-y-puertos).

### Local

Completa la [preparación local del backend](../01-api-karate/README.md#local) y ejecuta `npm.cmd ci` dentro de `VisionText-frontend/` para el perfil `web`.

```powershell
& '.\pruebas\02-rendimiento-jmeter\Ejecutar-JMeter.ps1' -Entorno local
```

El lanzador prepara las doce imágenes en un catálogo temporal en `127.0.0.1:8012` y sirve la compilación web en `127.0.0.1:4173`. Los perfiles `incremental`, `pico`, `sostenida` y `escritura` se ejecutan en el entorno local. Agrega `-Perfil carga` para repetir solo ese perfil.

### En conjunto

Ejecuta ambos entornos y compara `base` y `carga`, que usan las mismas consultas. El primer acceso y los perfiles exclusivos de local quedan en sus respectivos reportes. [Ejecución con las demás suites](../README.md#ejecutar-todo).

## Perfiles

| Perfil | Local | Desplegado | Qué mide |
| --- | --- | --- | --- |
| `inicio` | 1 petición | 1 petición | Primer acceso HTTP. Local también registra el arranque del proceso hasta salud HTTP 200. |
| `rutas` | 1 VU | 1 VU | Raíz, salud, OpenAPI, CORS, errores esperados 400/401/404/422 y endpoint APK. La API local con S3 responde el 404 previsto para la APK. |
| `base` | 1 VU × 3 | 1 VU × 3 | Búsquedas por texto e imagen, miniaturas y originales. |
| `carga` | 2 VU × 4 | 2 VU × 4 | Dos grupos concurrentes, uno por texto y otro por imagen. |
| `incremental` | Hasta 6 VU × 4, rampa de 12 s | | Comportamiento al incorporar usuarios gradualmente. |
| `pico` | Hasta 8 VU × 2, rampa de 1 s | | Respuesta ante la incorporación rápida de usuarios. |
| `sostenida` | Hasta 3 VU durante 75 s | | Búsquedas y descargas repetidas en una ventana continua. |
| `admin` | 2 VU × 3 | 1 VU × 1 | Un login por usuario, catálogo paginado y estado de almacenamiento. |
| `escritura` | 2 VU × 2 | | Subir, descargar y borrar cada imagen usando el ID devuelto, verificar el 404 posterior y contrastar conteos iniciales y finales. |
| `web` | 2 VU × 3 | 2 VU × 3 | Documento HTML y archivos JS y CSS correlacionados desde él. |

VU significa usuario virtual. El generador usa un modelo cerrado. Cada usuario espera la respuesta y la pausa antes de continuar. Las peticiones por segundo y el máximo de hilos concurrentes se obtienen del JTL.

## Evidencia y lectura

El [índice de resultados](reports/README.md) enlaza el JTL en formato CSV y el JSON de métricas de cada perfil. Cada nueva ejecución genera además el dashboard en `reports/<entorno>/<corrida>/<perfil>/html/index.html`. Para reconstruir un dashboard de la entrega sin volver a enviar peticiones, usa el JTL de ese perfil. En este ejemplo `JMETER_HOME` apunta a la instalación de JMeter y la carpeta de salida debe estar vacía o faltar.

```powershell
Push-Location .\pruebas\02-rendimiento-jmeter
& "$env:JMETER_HOME\bin\jmeter.bat" -q .\config\evidencia.properties `
  -g .\reports\local\20261118-150033-623716\carga\muestras.jtl -o .\target\dashboard-carga
Pop-Location
```

- **Datos.** `CSV Data Set Config` lee consultas, límites, umbrales y archivos para elefantes, alpacas y cebras. JMeter verifica que el resultado corresponda a la consulta y usa su ID para descargar la miniatura y el original.
- **Aserciones.** Cada petición verifica código HTTP y duración. Los flujos también comprueban JSON, cabeceras o formato de archivo según la ruta. Los 4xx esperados cuentan como éxito cuando cumplen las aserciones del caso.
- **Métricas.** El lanzador ejecuta JMeter sin interfaz con `-n`, registra con `-l`, usa el resumen de consola y genera HTML con `-e -o`. El dashboard muestra throughput, latencia, distribución de tiempos, percentiles y errores. Los presupuestos por operación y entorno están en `scripts/perfiles.py`. El resumen marca «REVISAR» al detectar muestras fallidas, faltantes o un p95 por encima del objetivo.
- **Comparación.** El primer acceso a Render se registra aparte y puede incluir el despertar del servicio. Compara los perfiles `base` y `carga` con las mismas consultas. Ten en cuenta que el despliegue usa un catálogo mayor y servicios remotos, y que en local el generador y la API comparten equipo. Una muestra individual da una referencia puntual, así que usa los perfiles con más peticiones para interpretar percentiles.

Los JMX de `plans/` se pueden abrir en la interfaz de JMeter para revisar los Thread Groups, el CSV y las aserciones. Si cambias un perfil en `scripts/perfiles.py` o `scripts/generar_planes.py`, regenera los JMX con `python pruebas/02-rendimiento-jmeter/scripts/generar_planes.py` desde `calidad/`.

[Manual de ejecución sin interfaz](https://jmeter.apache.org/usermanual/get-started#non_gui) y [manual del dashboard de JMeter](https://jmeter.apache.org/usermanual/generating-dashboard).
