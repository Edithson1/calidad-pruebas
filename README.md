# Pruebas de VisionText

Karate comprueba la API, JMeter mide el rendimiento, Selenium recorre la web en Brave y Appium prueba la aplicación de Android. Las ejecuciones guardadas son del 17 al 19 de noviembre de 2026, hora de Lima.

| Suite | Local | Desplegado | Evidencia |
| --- | --- | --- | --- |
| [Karate](01-api-karate/README.md) | 48 de 48 aprobadas, incluido el límite de inicio de sesión | 36 de 36 aprobadas | [Resultados de API](01-api-karate/reports/README.md) |
| [JMeter](02-rendimiento-jmeter/README.md) | 345 muestras válidas. 8 de 10 perfiles dentro del objetivo | 69 muestras válidas. 6 de 6 perfiles dentro del objetivo | [Métricas por entorno](02-rendimiento-jmeter/reports/README.md) |
| [Selenium](03-web-selenium/README.md) | 11 de 11 aprobadas | 8 de 8 aprobadas en la corrida completa | [Resultados web y capturas](03-web-selenium/reports/README.md) |
| [Appium](04-movil-appium/README.md) | 11 de 11 aprobadas | 9 de 9 aprobadas | [Resultados Android y capturas](04-movil-appium/README.md#resultados) |

## Carpetas en la computadora

Coloca las carpetas al mismo nivel. Los lanzadores buscan el código de VisionText junto a esta carpeta de pruebas. Los comandos de las guías parten de `calidad/` en PowerShell.

```text
calidad/
├── pruebas/                     # Este repositorio, con las cuatro suites y trazabilidad/
├── VisionText-backend/          # API, requirements-dev.txt, scripts/ y dataset_final/
├── VisionText-frontend/         # Web React, package.json, package-lock.json y src/
└── VisionText-android/          # Código Android, gradlew.bat, app/ y artifacts/VisionText.apk
```

Desde `calidad/`, clona las pruebas con el nombre que usan los comandos y consigue las carpetas de la aplicación que te falten.

```powershell
git clone https://github.com/Edithson1/calidad-pruebas.git pruebas
git clone https://github.com/Edithson1/VisionText-backend.git VisionText-backend
git clone https://github.com/Edithson1/visiontext-frontend.git VisionText-frontend
```

- **Backend.** Conserva `dataset_final/` con los nombres originales. JMeter lee doce JPEG de [`consultas.csv`](02-rendimiento-jmeter/data/consultas.csv). Selenium y Appium también toman muestras de ese catálogo. La [preparación local de Karate](01-api-karate/README.md#local) instala el entorno de Python y los modelos que comparten las cuatro suites. [Código del backend](https://github.com/Edithson1/VisionText-backend).
- **Frontend.** Usa `VisionText-frontend/` con la descarga de APK y la paginación de Admin. Con Node.js 22 instalado, ejecuta `npm.cmd ci` dentro de la carpeta antes de correr Selenium o JMeter en local. [Código del frontend](https://github.com/Edithson1/visiontext-frontend).
- **Android.** Copia `VisionText-android/` desde el proyecto del equipo para compilar en local. Para probar el despliegue basta la APK de distribución en `VisionText-android/artifacts/VisionText.apk` y el catálogo de imágenes del backend. [Descargar la APK de VisionText](https://visiontext-backend.onrender.com/api/app/download).

## Enlaces y puertos

| Servicio | Desplegado | Local durante las pruebas |
| --- | --- | --- |
| API | [Render](https://visiontext-backend.onrender.com/) · [Salud](https://visiontext-backend.onrender.com/api/health) · [OpenAPI](https://visiontext-backend.onrender.com/openapi.json) | `127.0.0.1:8011` para Karate, `:8012` para JMeter, `:8013` para Selenium y `:8014` para Appium |
| Web | [VisionText en Vercel](https://visiontext-sigma.vercel.app/) | `http://127.0.0.1:4173` en JMeter y `http://127.0.0.1:4174` en Selenium |
| Android | La APK release usa la API HTTPS de Render. [Ruta de descarga](https://visiontext-backend.onrender.com/api/app/download) | La APK debug usa `http://10.0.2.2:8014` desde el emulador |

En el despliegue, `VITE_API_URL` apunta a Render y `CORS_ORIGINS` incluye el origen de Vercel. Para probar en local, los lanzadores inician y cierran los servicios temporales y configuran la URL de la web o de la APK. Los reportes usan enlaces relativos desde el README de cada suite. En Jira, usa un enlace al archivo en el commit de la ejecución. [Configuración de Render](https://github.com/Edithson1/VisionText-backend/blob/main/DEPLOY-RENDER-DRIVE.md).

## Ejecutar todo

Prepara [Java y Maven](01-api-karate/README.md), [JMeter](02-rendimiento-jmeter/README.md), [Brave y Selenium](03-web-selenium/README.md) y [el emulador de Appium](04-movil-appium/README.md#preparar-otro-equipo-windows). Ejecuta los comandos en orden desde `calidad/`.

### Local

```powershell
& .\pruebas\01-api-karate\Ejecutar-Local.ps1
& .\pruebas\02-rendimiento-jmeter\Ejecutar-JMeter.ps1 -Entorno local
& .\pruebas\03-web-selenium\Ejecutar-Selenium.ps1 -Entorno local
& .\pruebas\04-movil-appium\Ejecutar-Appium.ps1 -Entorno local
```

Cada lanzador crea su catálogo y credenciales de prueba. Si JMeter marca un perfil como `REVISAR`, consulta sus métricas y continúa con las otras suites.

### Desplegado

Para cubrir las consultas de administración en Render, pide al equipo una cuenta autorizada. Cárgala en la sesión de PowerShell antes de los comandos.

```powershell
$cuentaQa = Get-Credential -Message 'Cuenta de VisionText para las pruebas en Render'
$env:VT_JMETER_ADMIN_USER = $cuentaQa.UserName
$env:VT_JMETER_ADMIN_PASSWORD = $cuentaQa.GetNetworkCredential().Password
$env:VT_WEB_USER = $env:VT_JMETER_ADMIN_USER
$env:VT_WEB_PASSWORD = $env:VT_JMETER_ADMIN_PASSWORD
$env:VT_APP_USER = $env:VT_JMETER_ADMIN_USER
$env:VT_APP_PASSWORD = $env:VT_JMETER_ADMIN_PASSWORD

& .\pruebas\01-api-karate\Ejecutar-Karate.ps1
& .\pruebas\02-rendimiento-jmeter\Ejecutar-JMeter.ps1 -Entorno render
& .\pruebas\03-web-selenium\Ejecutar-Selenium.ps1 -Entorno render
& .\pruebas\04-movil-appium\Ejecutar-Appium.ps1 -Entorno render
```

Cierra la sesión de PowerShell al terminar para descartar las variables. Karate público funciona sin cuenta. JMeter permite omitir `admin` con `-SoloPublico`.

### En conjunto

Completa el bloque local y después el desplegado. Revisa los resultados de cada suite por separado para distinguir los fallos de la aplicación, los problemas de conexión y los objetivos de tiempo. Usa la [guía de trazabilidad](trazabilidad/README.md) para llevar los casos y las evidencias a Jira.
