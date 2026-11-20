# Selenium para VisionText en Brave

La suite comprueba las búsquedas, la navegación, la descarga de la APK y los flujos de administración desde Brave. El 19 de noviembre de 2026 pasaron **11 de 11 casos en local** y **8 de 8 en la corrida completa de Vercel con Render**. Una repetición posterior quedó interrumpida por un tiempo de espera al conectar con Vercel. [JUnit, capturas y detalle de la repetición](reports/README.md).

## Preparar en Windows

Instala Brave y Python 3.13. Desde `calidad/` abre PowerShell y prepara el entorno de Selenium una vez.

```powershell
Push-Location .\pruebas\03-web-selenium
py -3.13 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
Pop-Location
```

El lanzador resuelve `Brave.lnk` y Selenium abre `brave.exe` con ChromeDriver. Para usar otra instalación, pasa `-Brave` con la ruta del acceso directo o del ejecutable. Selenium Manager puede descargar un controlador compatible. Para indicar un ChromeDriver instalado manualmente, usa `CHROMEDRIVER_PATH`. En la corrida guardada se usaron Chromium **158.0.8127.42** y ChromeDriver **158.0.8127.36**.

Para comprobar solo el arranque de Brave y las versiones, usa estos comandos desde `calidad/`.

```powershell
Push-Location .\pruebas\03-web-selenium
$env:BRAVE_BINARY = & .\Resolver-Brave.ps1
& .\.venv\Scripts\python.exe .\comprobar_brave.py
Pop-Location
```

## Ejecutar en Windows

### Desplegado

Desde `calidad/`, ejecuta contra Vercel y Render. Configura `VT_WEB_USER` y `VT_WEB_PASSWORD` con la cuenta de pruebas del despliegue o usa el archivo privado `VisionText-backend/.env.render`. La sesión administrativa consulta el catálogo.

```powershell
& '.\pruebas\03-web-selenium\Ejecutar-Selenium.ps1' -Entorno render
```

### Local

Completa la [preparación del backend](../01-api-karate/README.md#local), conserva `VisionText-backend/dataset_final/` y ejecuta `npm.cmd ci` en `VisionText-frontend/`. Vuelve a `calidad/` para lanzar la suite.

```powershell
& '.\pruebas\03-web-selenium\Ejecutar-Selenium.ps1' -Entorno local
```

El lanzador prepara un catálogo temporal de 32 imágenes y sirve la compilación de React en `http://127.0.0.1:4174`. Verifica que el catálogo, FAISS y RustFS recuperen sus conteos iniciales después de subir y eliminar la imagen de prueba.

### En conjunto

Ejecuta ambos comandos. `WEB-01` a `WEB-08` se prueban en ambos entornos y `WEB-09` a `WEB-11` en local. Agrega `-Visible` para ver Brave o `-Caso WEB_10` para repetir ese caso local. Cada caso usa un perfil de Brave independiente. [Ejecución con las demás suites](../README.md#ejecutar-todo).

## Casos de la suite

| ID | Flujo | Local | Desplegado |
| --- | --- | :---: | :---: |
| WEB-01 | Brave abre VisionText y cambia de sección | ✓ | ✓ |
| WEB-02 | Entrada vacía deshabilitada, búsqueda textual y apertura de la imagen original | ✓ | ✓ |
| WEB-03 | Vista previa, búsqueda visual y recuperación de una imagen conocida | ✓ | ✓ |
| WEB-04 | Eliminar la vista previa y rechazar un archivo de texto | ✓ | ✓ |
| WEB-05 | Protección de las pantallas Subir y Admin | ✓ | ✓ |
| WEB-06 | Menú de navegación en ventana estrecha | ✓ | ✓ |
| WEB-07 | Descarga y contenido básico de la APK publicada, o aviso local de disponibilidad | ✓ | ✓ |
| WEB-08 | Inicio de sesión, navegación entre páginas, persistencia al recargar y cierre de sesión | ✓ | ✓ |
| WEB-09 | Mensaje al iniciar sesión con credenciales incorrectas | ✓ | |
| WEB-10 | Seleccionar, describir, subir, comprobar en el catálogo, cancelar el borrado y confirmar el borrado | ✓ | |
| WEB-11 | Avisos de archivo inválido y de similitud insuficiente | ✓ | |

Los objetos de página usan IDs y atributos existentes de la interfaz, selectores CSS y etiquetas visibles. Las esperas explícitas sincronizan rutas, miniaturas cargadas, páginas de catálogo, cuadros de diálogo y descargas.

Cada nueva ejecución guarda `index.html`, `junit.xml` y capturas en `reports/<entorno>/<corrida>/`. El índice de la entrega reúne los XML y las capturas de los flujos principales. [Resultados de Selenium](reports/README.md).

[Configuración del navegador y Selenium Manager](https://www.selenium.dev/documentation/selenium_manager/) y [selección de ChromeDriver](https://developer.chrome.com/docs/chromedriver/downloads/version-selection).
