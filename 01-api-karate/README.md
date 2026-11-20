# Pruebas de API de VisionText con Karate DSL

La suite usa **Karate 1.5.2**, **JUnit 5** y **Java 21**. Ejecuta solicitudes HTTP contra la API en Render y contra una instancia local de VisionText con PostgreSQL, RustFS, CLIP y FAISS reales.

## Resultados

La corrida del 17 de noviembre de 2026 cubrió 52 escenarios distintos. Los casos comunes se repitieron en ambos entornos.

| Entorno | Resultado | Evidencia |
| --- | --- | --- |
| Render | 36 de 36 aprobados | [Publicación, búsquedas, descargas y validaciones](reports/README.md#render) |
| Local | 47 de 47 aprobados | [Integración con el catálogo temporal](reports/README.md#local) |
| Local, límite de inicio de sesión | 1 de 1 aprobado | [Bloqueo temporal y recuperación](reports/README.md#local) |

## Ejecutar en Windows

Instala Java 21 y Maven. El lanzador busca Java en Android Studio o `JAVA_HOME`, y Maven en el `PATH` o IntelliJ IDEA. Si hace falta, configura `VT_KARATE_JAVA_HOME` con la carpeta del JDK y `VT_KARATE_MAVEN` con la ruta completa a `mvn.cmd`. Ejecuta desde `calidad/` en PowerShell.

### Desplegado

```powershell
& '.\pruebas\01-api-karate\Ejecutar-Karate.ps1'
```

El perfil `publico` usa la API de Render y funciona sin credenciales. También puedes ejecutar `mvn test` desde esta carpeta con Java 21. La primera ejecución descarga dependencias de Maven Central. Con la caché preparada, agrega `-SinDescargas` al lanzador. [API de VisionText](https://visiontext-backend.onrender.com/).

### Local

Prepara `VisionText-backend/` según la [estructura del proyecto](../README.md#carpetas-en-la-computadora). Con Python 3.12 instalado, ejecuta una vez desde `calidad/`.

```powershell
Push-Location .\VisionText-backend
py -3.12 -m venv .venv\windows
& .\.venv\windows\Scripts\python.exe -m pip install -r requirements-dev.txt
& .\.venv\windows\Scripts\python.exe .\scripts\prepare_onnx.py --directory model_cache/onnx
Pop-Location
```

Coloca `rustfs.exe` para Windows x64 en `VisionText-backend/.venv/rustfs/rustfs.exe`. Se usó la versión 1.0.3. [Descarga de RustFS](https://github.com/rustfs/rustfs/releases/tag/1.0.3).

El lanzador usa PostgreSQL 16 en Ubuntu WSL. Si ya tienes PostgreSQL portátil en `~/.local/share/visiontext-postgres/portable`, se usa esa copia. En un equipo nuevo, instala Ubuntu 24.04 con `wsl --install -d Ubuntu-24.04`, termina su configuración y ejecuta en Ubuntu `sudo apt update` y `sudo apt install postgresql-16`. En PowerShell usa el nombre de distribución que muestre `wsl -l -q`. [Instalación de PostgreSQL en Ubuntu](https://ubuntu.com/server/docs/how-to/databases/install-postgresql/).

```powershell
$env:VT_QA_WSL_DISTRO = 'Ubuntu-24.04' # Solo si tu distribución tiene este nombre
& '.\pruebas\01-api-karate\Ejecutar-Local.ps1'
```

El lanzador levanta PostgreSQL, RustFS y la API en `127.0.0.1:8011`, con un catálogo vacío y credenciales temporales. Ejecuta primero `local` y luego `limite-login`. Al terminar detiene los servicios y elimina el clúster temporal. Los registros de arranque quedan en `target/local-*`. Si hay puertos ocupados, usa `-ApiPort`, `-PostgresPort` o `-StoragePort`.

Si ya tienes otra instancia local aislada con S3, configura `VT_KARATE_URL`, `VT_KARATE_ADMIN_USER`, `VT_KARATE_ADMIN_PASSWORD` y `VT_KARATE_LOCAL_ISOLATED=1`, y ejecuta `mvn '-Dkarate.env=local' test`. Puedes configurar por separado el origen de imágenes en `VT_KARATE_ASSET_ORIGIN` y el origen admitido en `VT_KARATE_CORS_ORIGIN`.

### En conjunto

Ejecuta ambos lanzadores. Compara los resultados de los casos `@comun` en los dos ambientes y revisa por separado los casos de catálogo de Render y los de escritura local. [Ejecución con las demás suites](../README.md#ejecutar-todo).

## Cobertura

| Casos | Qué comprueban | Códigos |
| --- | --- | --- |
| SRV-01 a SRV-05 | Identidad, salud, paridad entre registros y vectores, rutas OpenAPI y CORS | 200, 400 |
| TXT-01 a TXT-10 | Búsqueda por texto, límite de resultados, esquema, consulta vacía/ausente/larga, tipos, rangos y JSON ilegible | 200, 422 |
| IMG-01 a IMG-09 | Búsqueda multipart, límites, umbrales, MIME, bytes inválidos, tamaño en píxeles y parte ausente | 200, 400, 413, 422 |
| CAT-01 a CAT-05 | Coincidencias semánticas en Render, recuperación de una imagen conocida, consulta sin coincidencias, JPEG y miniatura, ID inexistente | 200, 404 |
| APK-01 y APK-02 | Descarga APK con entradas del ZIP y cabeceras verificadas, o error si el proveedor local es S3 | 200, 404 |
| AUTH-01 a AUTH-06 | Rutas protegidas, token inválido y formulario de login incompleto | 401, 422 |
| ADM-01 a ADM-08 | Login Android y web, uso del JWT, URL de miniatura, almacenamiento S3, parámetros y borrado inexistente | 200, 401, 404, 422 |
| UPL-01 a UPL-05 | Tipo de archivo, píxeles, parte ausente, nombre restringido y baja similitud | 400, 413, 422 |
| CIC-01 | Subida con y sin descripción, paginación, búsqueda, descarga, borrado, ausencia posterior y vuelta a los conteos iniciales | 200, 404 |
| RATE-01 | Intentos incorrectos, bloqueo, `Retry-After` y login correcto al salir del bloqueo | 200, 401, 429 |

Los esquemas en `schemas/` revisan campos, tipos, rangos y nulabilidad. Las búsquedas también validan orden por similitud, IDs únicos, límites y correspondencia entre cada ID y su URL. Los casos parametrizan consultas desde JSON, generan UUID propios, reutilizan la sesión con `callonce` y encadenan el ID que devuelve la subida en las consultas, descargas y borrado. Los helpers se reutilizan con `call`. El gancho `afterScenario` limpia los archivos temporales identificados durante el escenario si alguna aserción falla.

La imagen pequeña corresponde a `african_elephant_african_elephant-0005.jpg` del catálogo VisionText. El PNG sintético de 2048 × 2048 permite probar el límite de píxeles con un archivo pequeño.

## Tiempos y evidencia

Cada petición relevante comprueba `responseTime` en milisegundos. Los presupuestos están en `karate-config.js`.

| Petición | Render | Local |
| --- | ---: | ---: |
| Raíz y salud inicial, incluye posible arranque en frío | 155 s | 10 s |
| Contrato, CORS, validaciones, administración y salud durante el ciclo | 15 s | 5 s |
| Búsqueda e inferencia CLIP | 40 s | 15 s |
| Descarga o transferencia | 40 s | 15 s |
| Subida válida | | 25 s |

Son límites funcionales para detectar esperas anómalas. La medición de rendimiento con concurrencia corresponde a JMeter.

Al volver a correr Karate, abre `reports/<perfil>/karate-summary.html`. Cada caso enlaza las aserciones, los códigos HTTP y los tiempos. También se generan XML JUnit y JSON Cucumber. Los resultados publicados conservan el nombre, estado y duración de cada escenario. [Resultado por archivo y entorno](reports/README.md).
