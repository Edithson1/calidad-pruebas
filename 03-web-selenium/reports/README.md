# Evidencias de Selenium con Brave

Las dos ejecuciones completas del **19 de noviembre de 2026** registraron 19 aprobaciones de 11 casos distintos. Ocho casos se ejecutaron en ambos entornos.

| Entorno | Resultado | Evidencia |
| --- | --- | --- |
| Local aislado | 11 de 11 aprobados | [JUnit](local/20261119-160232-035264/junit.xml) · [Catálogo antes y después](local/20261119-160232-035264/entorno.json) |
| Vercel con API en Render | 8 de 8 aprobados | [JUnit](render/20261119-155525-581671/junit.xml) · [Versiones de Brave y ChromeDriver](render/20261119-155525-581671/navegador.json) |

La descarga produjo una APK de 682 054 bytes en Brave. Selenium comprobó el manifiesto y `classes.dex`. El flujo de administración también recorrió dos páginas del catálogo. [Descarga de la APK](render/20261119-155525-581671/capturas/WEB-07-passed.png) · [Segunda página del catálogo](render/20261119-155525-581671/capturas/WEB-08-pagina-2.png).

En local los conteos volvieron a 32 registros, 32 vectores, 32 originales y 32 miniaturas después de la prueba de escritura. [Subida exitosa](local/20261119-160232-035264/capturas/WEB-10-subida.png) · [Confirmación del borrado](local/20261119-160232-035264/capturas/WEB-10-confirmacion.png).

En una repetición posterior del despliegue, [Brave registró un timeout de conexión a Vercel](render/20261119-160205-141826/capturas/WEB-01-failed.png). Una conexión HTTP directa también agotó el tiempo de espera. Esa repetición se interrumpió y la tabla enlaza a la ejecución completa anterior.

[Guía, casos y comandos](../README.md).
