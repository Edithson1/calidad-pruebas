# Pruebas de VisionText Android con Appium

La suite automatiza la APK en el emulador dedicado `VisionText_QA` con Android 14 (API 34, AOSP x86_64), Appium 3.9.1, UiAutomator2 8.6.0 y Python 3.13. El lanzador inicia Android y Appium desde PowerShell y cierra sus procesos al terminar.

## Resultados

El 19 de noviembre de 2026 se completaron las dos corridas. Los XML muestran el resultado y la duración de cada caso. El JSON de entorno identifica la APK por nombre y SHA-256.

| Entorno | Resultado | Evidencia |
| --- | --- | --- |
| Local con APK debug | 11 de 11 aprobados | [JUnit](reports/local/20261119-201834-54301b/junit.xml) · [APK y entorno](reports/local/20261119-201834-54301b/entorno.json) |
| Render con APK publicada | 9 de 9 aprobados | [JUnit](reports/render/20261119-201258-f43497/junit.xml) · [APK y entorno](reports/render/20261119-201258-f43497/entorno.json) |

- **APP-03.** En Render el gesto de desplazamiento cambió las tarjetas visibles y se abrió la imagen original. [Antes del gesto](reports/render/20261119-201258-f43497/capturas/APP-03-resultados-antes-del-swipe.png) · [Después del gesto](reports/render/20261119-201258-f43497/capturas/APP-03-resultados-despues-del-swipe.png).
- **APP-04 y APP-09.** La búsqueda visual recuperó el mismo JPEG y el catálogo pasó a la segunda página. [Coincidencia de imagen](reports/render/20261119-201258-f43497/capturas/APP-04-coincidencia-exacta.png) · [Paginación](reports/render/20261119-201258-f43497/capturas/APP-09-catalogo-pagina-dos.png).
- **APP-11.** En local se subió un JPEG temporal y se confirmó su eliminación. [Subida](reports/local/20261119-201834-54301b/capturas/APP-11-subida-confirmada.png) · [Confirmación](reports/local/20261119-201834-54301b/capturas/APP-11-confirmacion-eliminar.png).

## Ejecutar en Windows

Completa la [preparación del emulador](#preparar-otro-equipo-windows) y abre PowerShell en `calidad/`.

### Desplegado

Guarda la APK de distribución como `VisionText-android/artifacts/VisionText.apk`. Conserva el JPEG `african_elephant_african_elephant-0005.jpg` en `VisionText-backend/dataset_final/` para la búsqueda por imagen. Usa `VT_APP_USER` y `VT_APP_PASSWORD` o el archivo privado `VisionText-backend/.env.render` para el caso de consulta del catálogo. [Descargar APK](https://visiontext-backend.onrender.com/api/app/download).

```powershell
& .\pruebas\04-movil-appium\Ejecutar-Appium.ps1 -Entorno render
```

### Local

Prepara el [backend temporal](../01-api-karate/README.md#local), conserva el catálogo de imágenes y el código de `VisionText-android/`. La compilación debug requiere Android SDK 36. El lanzador prepara 12 imágenes y conecta el emulador a la API de Windows por `http://10.0.2.2:8014`.

```powershell
& .\pruebas\04-movil-appium\Ejecutar-Appium.ps1 -Entorno local
```

### En conjunto

Ejecuta los dos comandos. `APP-01` a `APP-09` se prueban con ambas APK. `APP-10` y `APP-11` usan el catálogo local. Agrega `-Caso APP-03` para repetir solo la búsqueda y el gesto. Las nuevas ejecuciones crean `reporte.html`, `junit.xml`, `entorno.json`, capturas y bitácoras en `reports/<entorno>/<corrida>/`. [Ejecución con las demás suites](../README.md#ejecutar-todo).

Para ejecutar solo la comprobación de arranque y navegación, usa `& .\pruebas\04-movil-appium\Verificar-Appium.ps1`. Guarda la captura en `evidence/appium-navegacion.png`.

## Casos

| Caso | Validación | Entorno |
| --- | --- | --- |
| APP-01 | Abre la app nativa y recorre Texto, Imagen, Subir y Admin. | Render y local |
| APP-02 | Una búsqueda con espacios muestra una validación. | Render y local |
| APP-03 | Busca «African elephant», verifica que el deslizamiento cambie las tarjetas visibles, abre el original y vuelve a la lista. | Render y local |
| APP-04 | Selecciona un JPEG con el selector de Android, comprueba la vista previa y recupera la misma imagen en el catálogo. | Render y local |
| APP-05 | Cancela el selector, vuelve a seleccionar un archivo y lo quita. | Render y local |
| APP-06 | Comprueba que Subir y Admin piden autenticación y que el formulario rechaza campos vacíos. | Render y local |
| APP-07 | Intenta guardar una URL inválida y confirma que se conserva la configuración. | Render y local |
| APP-08 | Usa el botón Probar para consultar la API y verifica que el ajuste se conserva al reiniciar la app. | Render y local |
| APP-09 | Inicia sesión, consulta el catálogo, navega entre páginas si el catálogo supera 30 registros y verifica el cierre de sesión. | Render y local |
| APP-10 | Verifica el error de credenciales incorrectas. | Local |
| APP-11 | Sube un JPEG temporal, comprueba el alta, cancela la primera confirmación y luego elimina solo ese archivo. | Local |

Las capacidades se definen en `config/sesion.py`. Los controles se localizan por su identificador de accesibilidad, texto nativo o ID de Android. La suite usa esperas explícitas y ejecuta el gesto con `mobile: swipeGesture`. El caso APP-03 captura la lista antes y después del gesto y comprueba que la imagen original se haya cargado.

## Preparar otro equipo Windows

Instala Android Studio con el SDK, Android Emulator, Platform-Tools y las herramientas de línea de comandos en `cmdline-tools/latest`. El lanzador busca el Java 21 de Android Studio y Node 22.16.0 en `$env:LOCALAPPDATA/nvm/v22.16.0`. Instala esa versión con NVM para Windows y ten Python 3.13 disponible. En SDK Manager instala **Android 14 → x86_64 System Image** o el paquete `system-images;android-34;default;x86_64` con `sdkmanager`. Habilita la virtualización para el emulador.

Desde la raíz de VisionText ejecuta una vez estos comandos.

```powershell
Push-Location .\pruebas\04-movil-appium
$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$qaNode = "$env:LOCALAPPDATA\nvm\v22.16.0"
$env:Path = "$qaNode;$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:Path"
$env:APPIUM_HOME = Join-Path (Get-Location).Path '.appium'

npm.cmd install --prefix . --no-save --no-package-lock appium@3.9.1
$appium = '.\node_modules\.bin\appium.cmd'
& $appium driver install uiautomator2@8.6.0
& $appium driver doctor uiautomator2
py -3.13 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
Pop-Location
```

La primera ejecución crea `VisionText_QA` en `target/avd`. Cada ejecución arranca el dispositivo en modo de solo lectura. Para el perfil local prepara los requisitos de WSL, PostgreSQL y almacenamiento descritos en la [guía de Karate](../01-api-karate/README.md).

[Requisitos de Appium](https://appium.io/docs/en/latest/quickstart/requirements/) · [Capacidades de UiAutomator2](https://appium.github.io/appium-uiautomator2-driver/latest/reference/capabilities/) · [Emulador de Android desde la terminal](https://developer.android.com/studio/run/emulator-commandline)
