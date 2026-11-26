# Fichas de casos de Selenium (DOC-04)

Una ficha por caso, de `WEB-01` a `WEB-11`. Los datos salen de [`tests/test_visiontext.py`](tests/test_visiontext.py), del Page Object [`pages/visiontext.py`](pages/visiontext.py), de [`conftest.py`](conftest.py), de [`ejecutar.py`](ejecutar.py) y de los archivos de cada corrida. Jira: [VTQA-59](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-59).

## Corridas de referencia

| Entorno | Fecha (hora de Lima) | Resultado | Navegador | Evidencia |
| --- | --- | --- | --- | --- |
| Desplegado: web en Vercel y API en Render | 25-nov-2026 19:34:45 | 8 de 8 aprobados en 80,7 s | Brave (Chromium 158.0.8127.42), ChromeDriver 158.0.8127.88, ventana visible | [JUnit](reports/render/20261125-193445-006410/junit.xml) · [entorno](reports/render/20261125-193445-006410/entorno.json) · [navegador](reports/render/20261125-193445-006410/navegador.json) · [capturas](reports/render/20261125-193445-006410/capturas/) |
| Local aislado | 19-nov-2026 16:02:32 | 11 de 11 aprobados en 119,3 s | Brave (Chromium 158.0.8127.42), ChromeDriver 158.0.8127.36, sin ventana | [JUnit](reports/local/20261119-160232-035264/junit.xml) · [entorno y conteos](reports/local/20261119-160232-035264/entorno.json) · [navegador](reports/local/20261119-160232-035264/navegador.json) |

- **Versión de VisionText:** ninguna de las dos corridas guarda el commit ni la versión del frontend o del backend.
- **Herramientas:** Python 3.13, selenium 4.53.0, pytest 9.2.0 y pytest-html 4.2.0, según [`requirements.txt`](requirements.txt). En la corrida del 25-nov, el reporte HTML registra Python 3.13.4 en Windows 11.
- **Capturas locales:** de la corrida local solo están en el repositorio las de `WEB-10`. El resto de los casos locales tiene únicamente el JUnit.
- **Una repetición desplegada del 19-nov** se cortó por un timeout al conectar con Vercel ([VTQA-54](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-54)). Ese registro está en [reports/README.md](reports/README.md).

## Precondiciones comunes

- Brave y el entorno `.venv` instalados con `requirements.txt`. `Resolver-Brave.ps1` define `BRAVE_BINARY`. Cada caso abre un perfil limpio de Brave en una ventana de 1360 × 980, con una carpeta de descargas temporal.
- **Desplegado:** la cuenta de pruebas viene de `VT_WEB_USER`/`VT_WEB_PASSWORD` o de `VisionText-backend/.env.render`. Las credenciales no se escriben en los reportes ni en Jira. Antes de empezar, `ejecutar.py` exige que `/api/health` responda `healthy` y que los registros coincidan con los vectores. El 25-nov había 1575 y 1575, con almacenamiento `google_drive`.
- **Local:** `Ejecutar-Selenium.ps1 -Entorno local` levanta, mediante el lanzador de Karate, una API aislada en `127.0.0.1:8013` con S3 y un catálogo vacío. Después carga 32 imágenes de `dataset_final` (11 `african_elephant_`, 11 `alpaca_` y 10 `zebra_`). Compila la web y la sirve en `127.0.0.1:4174`. Al final compara los conteos de registros, vectores, originales y miniaturas de antes y después: el 19-nov fueron 32 en los cuatro, antes y después.
- **Datos de entrada:** [`data/african_elephant_african_elephant-0005.jpg`](data/african_elephant_african_elephant-0005.jpg) y [`data/archivo-invalido.txt`](data/archivo-invalido.txt). En la corrida local del 19-nov la imagen se leía desde `VisionText-backend/dataset_final/`; desde el commit `1695ae1` se lee desde `data/`.

## Cómo se localizan y sincronizan los elementos

- **Selectores:** se usan IDs (`#image-upload`, `#file-upload`), CSS por atributos (`img[alt="Preview"]`, `button[title="Eliminar imagen"]`, `nav[aria-label="Paginación de imágenes"]`, `aside[aria-label="Aplicación Android"] [role="status"]`) y XPath relativos por texto visible (`//button[normalize-space(.)="…"]`). No hay XPath absolutos.
  - **Riesgo:** varios localizadores dependen de textos de la interfaz. Si cambia un texto, hay que actualizar el Page Object.
- **Esperas:** son todas explícitas, con `WebDriverWait`: 90 s en el despliegue y 35 s en local, con sondeo cada 0,25 s e ignorando `StaleElementReferenceException`. Esperan visibilidad, que el elemento sea pulsable, textos, invisibilidad, imágenes cargadas (`complete` y `naturalWidth`) y que cambien las filas de la paginación. No hay esperas implícitas. La carga de página tiene un límite de 45 s y los scripts de 15 s.
- **Evidencia automática:** `conftest.py` guarda una captura `WEB-XX-<resultado>.png` al terminar cada caso. Algunos casos guardan además capturas intermedias.

---

## WEB-01 · Brave abre VisionText y cambia de sección

| Jira | Código | Entornos |
| --- | --- | --- |
| [VTQA-29](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-29) | [test_WEB_01](tests/test_visiontext.py#L37) | Local y desplegado |

**Precondiciones:** las comunes; no requiere sesión.
**Datos:** ninguno.
**Pasos:**
1. Abrir el inicio y esperar el título "VisionText AI".
2. Ejecutar `navigator.brave.isBrave()`.
3. Comprobar el encabezado "Encuentra la imagen perfecta".
4. Pulsar "Imagen" en el menú.
5. Pulsar "Texto".

**Resultado esperado:** `isBrave()` devuelve verdadero. "Imagen" lleva a `/image-search` con "Búsqueda por Imagen". "Texto" lleva a `/text-search` con "Encuentra la imagen perfecta".

| Ejecución | Resultado | Duración | Captura |
| --- | --- | --- | --- |
| Desplegado 25-nov | Aprobado | 4,111 s | [WEB-01-passed.png](reports/render/20261125-193445-006410/capturas/WEB-01-passed.png) |
| Local 19-nov | Aprobado | 6,038 s | No guardada en el repositorio |

## WEB-02 · Entrada vacía deshabilitada, búsqueda textual y apertura del original

| Jira | Código | Entornos |
| --- | --- | --- |
| [VTQA-30](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-30) | [test_WEB_02](tests/test_visiontext.py#L49) | Local y desplegado |

**Precondiciones:** las comunes; el catálogo debe tener imágenes `african_elephant_*`.
**Datos:** las consultas `""`, `"   "` y `"African elephant"`.
**Pasos:**
1. Con el campo vacío, comprobar que "Buscar" está deshabilitado.
2. Escribir tres espacios y volver a comprobarlo.
3. Buscar "African elephant".
4. Esperar el texto "Encontrados N resultados" y una miniatura `african_elephant_*` cargada desde `/api/thumbnails/`.
5. Pulsar el título del resultado.
6. Pasar a la pestaña nueva y esperar la imagen.

**Resultado esperado:** el botón sigue deshabilitado en los pasos 1 y 2. N es al menos 1. La pestaña nueva abre `/api/images/…` con el mismo identificador que la miniatura, y la imagen carga.

| Ejecución | Resultado | Duración | Capturas |
| --- | --- | --- | --- |
| Desplegado 25-nov | Aprobado | 21,310 s | [WEB-02-original.png](reports/render/20261125-193445-006410/capturas/WEB-02-original.png) · [WEB-02-passed.png](reports/render/20261125-193445-006410/capturas/WEB-02-passed.png) |
| Local 19-nov | Aprobado | 10,468 s | No guardadas en el repositorio |

## WEB-03 · Vista previa, búsqueda visual y recuperación de una imagen conocida

| Jira | Código | Entornos |
| --- | --- | --- |
| [VTQA-31](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-31) | [test_WEB_03](tests/test_visiontext.py#L77) | Local y desplegado |

**Precondiciones:** las comunes; la imagen de ejemplo debe estar en el catálogo.
**Datos:** `african_elephant_african_elephant-0005.jpg`.
**Pasos:**
1. Ir a "Imagen".
2. Cargar la imagen en `#image-upload`.
3. Esperar la vista previa.
4. Pulsar "Buscar Similares".

**Resultado esperado:** aparece "Resultados Similares" y una miniatura con `alt` igual a `african_elephant_african_elephant-0005.jpg`, cargada desde `/api/thumbnails/`.

| Ejecución | Resultado | Duración | Captura |
| --- | --- | --- | --- |
| Desplegado 25-nov | Aprobado | 16,888 s | [WEB-03-passed.png](reports/render/20261125-193445-006410/capturas/WEB-03-passed.png) |
| Local 19-nov | Aprobado | 10,243 s | No guardada en el repositorio |

## WEB-04 · Eliminar la vista previa y rechazar un archivo de texto

| Jira | Código | Entornos |
| --- | --- | --- |
| [VTQA-32](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-32) | [test_WEB_04](tests/test_visiontext.py#L87) | Local y desplegado |

**Precondiciones:** las comunes.
**Datos:** el JPEG de ejemplo y `archivo-invalido.txt`.
**Pasos:**
1. Ir a "Imagen" y cargar el JPEG.
2. Esperar la vista previa.
3. Pulsar "Eliminar imagen".
4. Cargar `archivo-invalido.txt`.

**Resultado esperado:** al quitar la imagen aparece "La vista previa aparecerá aquí". Con el .txt aparece "Por favor selecciona un archivo de imagen válido" y no se muestran ni el botón "Buscar Similares" ni la vista previa.

| Ejecución | Resultado | Duración | Captura |
| --- | --- | --- | --- |
| Desplegado 25-nov | Aprobado | 4,376 s | [WEB-04-passed.png](reports/render/20261125-193445-006410/capturas/WEB-04-passed.png) |
| Local 19-nov | Aprobado | 6,216 s | No guardada en el repositorio |

## WEB-05 · Protección de las pantallas Subir y Admin

| Jira | Código | Entornos |
| --- | --- | --- |
| [VTQA-33](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-33) | [test_WEB_05](tests/test_visiontext.py#L100) | Local y desplegado |

**Precondiciones:** las comunes; sin sesión iniciada.
**Datos:** ninguno.
**Pasos:**
1. Pulsar "Subir".
2. Abrir `/admin` escribiendo la ruta directamente.

**Resultado esperado:** en `/upload` aparecen "Panel de Administración" y "Subir imágenes requiere una cuenta de administrador", sin `#file-upload`. En `/admin` aparece el campo de contraseña y no hay tabla del catálogo.

| Ejecución | Resultado | Duración | Captura |
| --- | --- | --- | --- |
| Desplegado 25-nov | Aprobado | 4,452 s | [WEB-05-passed.png](reports/render/20261125-193445-006410/capturas/WEB-05-passed.png) |
| Local 19-nov | Aprobado | 5,629 s | No guardada en el repositorio |

## WEB-06 · Menú de navegación en ventana estrecha

| Jira | Código | Entornos |
| --- | --- | --- |
| [VTQA-34](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-34) | [test_WEB_06](tests/test_visiontext.py#L111) | Local y desplegado |

**Precondiciones:** las comunes.
**Datos:** una ventana de 470 × 920.
**Pasos:**
1. Cambiar el tamaño de la ventana.
2. Abrir el inicio y comprobar que `window.innerWidth` es menor de 768.
3. Pulsar el único botón visible del encabezado.
4. Elegir "Búsqueda por Imagen".

**Resultado esperado:** aparece "Búsqueda por Imagen" en `/image-search` y la opción del menú deja de verse.

| Ejecución | Resultado | Duración | Captura |
| --- | --- | --- | --- |
| Desplegado 25-nov | Aprobado | 4,130 s | [WEB-06-passed.png](reports/render/20261125-193445-006410/capturas/WEB-06-passed.png) |
| Local 19-nov | Aprobado | 6,227 s | No guardada en el repositorio |

## WEB-07 · Descarga de la APK o aviso de disponibilidad

| Jira | Código | Entornos |
| --- | --- | --- |
| [VTQA-35](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-35) | [test_WEB_07](tests/test_visiontext.py#L128) | Local y desplegado, con resultados distintos |

**Precondiciones:** las comunes; una carpeta de descargas temporal.
**Datos:** ninguno.
**Pasos:**
1. Pulsar "Descargar app (APK)".
2. Esperar el aviso.
3. En el despliegue, revisar el archivo descargado.

**Resultado esperado:**
- **Desplegado:** aparece "APK enviada al navegador" y se descarga `VisionText.apk`, un ZIP válido que contiene `AndroidManifest.xml` y `classes.dex`.
- **Local:** aparece una alerta que dice que la descarga "requiere el almacenamiento de Drive", y no se descarga ningún archivo.

| Ejecución | Resultado | Duración | Captura |
| --- | --- | --- | --- |
| Desplegado 25-nov | Aprobado | 5,835 s | [WEB-07-passed.png](reports/render/20261125-193445-006410/capturas/WEB-07-passed.png) |
| Local 19-nov | Aprobado | 5,595 s | No guardada en el repositorio |

## WEB-08 · Inicio de sesión, paginación, persistencia al recargar y cierre de sesión

| Jira | Código | Entornos |
| --- | --- | --- |
| [VTQA-36](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-36) | [test_WEB_08](tests/test_visiontext.py#L144) | Local y desplegado |

**Precondiciones:** las comunes; la cuenta de administrador de pruebas y un catálogo con más de 30 imágenes (había 32 en local y 1575 en el despliegue).
**Datos:** la cuenta de pruebas, tomada de las variables de entorno.
**Pasos:**
1. Entrar a Admin e iniciar sesión.
2. Leer los IDs de la página 1.
3. Pulsar "Siguiente".
4. Pulsar "Anterior".
5. Recargar.
6. Pulsar "Cerrar Sesión".
7. Recargar.

**Resultado esperado:**
- Aparece "Cerrar Sesión".
- La página 1 tiene 30 IDs distintos y "Anterior" está deshabilitado.
- La página 2 tiene entre 1 y 30 IDs, ninguno repetido de la página 1.
- Al volver con "Anterior" y al recargar se ven los mismos IDs de la página 1.
- Después de cerrar sesión y recargar sigue el formulario de acceso, sin tabla.

| Ejecución | Resultado | Duración | Capturas |
| --- | --- | --- | --- |
| Desplegado 25-nov | Aprobado | 18,997 s | [WEB-08-pagina-2.png](reports/render/20261125-193445-006410/capturas/WEB-08-pagina-2.png) · [WEB-08-passed.png](reports/render/20261125-193445-006410/capturas/WEB-08-passed.png) |
| Local 19-nov | Aprobado | 13,004 s | No guardadas en el repositorio |

## WEB-09 · Mensaje al iniciar sesión con credenciales incorrectas

| Jira | Código | Entornos |
| --- | --- | --- |
| [VTQA-19](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-19) | [test_WEB_09](tests/test_visiontext.py#L166) | Solo local (`solo_local`) |

**Precondiciones:** las comunes del entorno local; sin sesión iniciada. Según `pytest.ini`, la marca `solo_local` se describe así: "requiere catálogo aislado para validar credenciales incorrectas o escrituras".
**Datos:** el usuario de pruebas con una contraseña aleatoria (`uuid4().hex`).
**Pasos:**
1. Ir a Admin.
2. Iniciar sesión con la contraseña incorrecta.

**Resultado esperado:** aparece "Credenciales incorrectas" y no se muestra la tabla del catálogo.

| Ejecución | Resultado | Duración | Captura |
| --- | --- | --- | --- |
| Local 19-nov | Aprobado | 6,663 s | No guardada en el repositorio |
| Desplegado | No aplica | | |

## WEB-10 · Subir y eliminar una imagen temporal con confirmación

| Jira | Código | Entornos |
| --- | --- | --- |
| [VTQA-20](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-20) | [test_WEB_10](tests/test_visiontext.py#L175) | Solo local (`solo_local`) |

**Precondiciones:** las comunes del entorno local, con el catálogo temporal de 32 imágenes.
**Datos:** una copia del JPEG de ejemplo con el nombre `selenium-<uuid>.jpg` y la descripción "a photo of an African elephant".
**Pasos:**
1. Ir a "Subir" e iniciar sesión.
2. Seleccionar el archivo y esperar su vista previa (`blob:`).
3. Escribir la descripción y pulsar "Subir 1 imagen".
4. Ir a Admin y localizar la fila con la miniatura y la descripción.
5. Pulsar "Eliminar" y luego "Cancelar".
6. Pulsar "Eliminar" de nuevo y confirmar en "Confirmar Eliminación".

**Resultado esperado:**
- Aparecen "Resultados de la subida" y el mensaje "<archivo> … subida exitosamente".
- La fila del catálogo contiene la descripción.
- Al pulsar "Cancelar", el cuadro se cierra.
- Al confirmar, el catálogo vuelve a mostrarse sin esa fila.
- `ejecutar.py` encuentra los mismos conteos antes y después.

| Ejecución | Resultado | Duración | Capturas |
| --- | --- | --- | --- |
| Local 19-nov | Aprobado. Conteos de 32 registros, 32 vectores, 32 originales y 32 miniaturas, antes y después | 19,223 s | [WEB-10-subida.png](reports/local/20261119-160232-035264/capturas/WEB-10-subida.png) · [WEB-10-confirmacion.png](reports/local/20261119-160232-035264/capturas/WEB-10-confirmacion.png) |
| Desplegado | No aplica | | |

## WEB-11 · Avisos de archivo inválido y de similitud insuficiente

| Jira | Código | Entornos |
| --- | --- | --- |
| [VTQA-21](https://upch-team-lrowswbh.atlassian.net/browse/VTQA-21) | [test_WEB_11](tests/test_visiontext.py#L206) | Solo local (`solo_local`) |

**Precondiciones:** las comunes del entorno local.
**Datos:** `archivo-invalido.txt` y una copia del JPEG de ejemplo con la descripción "a studio photo of a close-up of a computer microprocessor on a printed circuit board".
**Pasos:**
1. Ir a "Subir" e iniciar sesión.
2. Seleccionar el .txt.
3. Seleccionar el JPEG y escribir la descripción.
4. Pulsar "Subir 1 imagen".

**Resultado esperado:** con el .txt aparece "Algunos archivos no son imágenes válidas y fueron ignorados" y no se ofrece "Subir 1 imagen". Al subir el JPEG aparecen "Resultados de la subida" y un mensaje que empieza por "Similitud insuficiente:".

| Ejecución | Resultado | Duración | Captura |
| --- | --- | --- | --- |
| Local 19-nov | Aprobado | 11,728 s | No guardada en el repositorio |
| Desplegado | No aplica | | |
