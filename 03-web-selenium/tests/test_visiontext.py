import os
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit
from uuid import uuid4
from zipfile import ZipFile, is_zipfile

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.visiontext import button, named

SUITE = Path(__file__).resolve().parents[1]
SAMPLE = SUITE.parents[1] / "VisionText-backend" / "dataset_final" / "african_elephant_african_elephant-0005.jpg"
INVALID = SUITE / "data" / "archivo-invalido.txt"


def matching_picture(filename):
    return By.CSS_SELECTOR, f'img[alt="{filename}"][src*="/api/thumbnails/"]'


def copy_sample(folder):
    path = folder / f"selenium-{uuid4().int}.jpg"
    shutil.copyfile(SAMPLE, path)
    return path


def open_admin(page, credentials):
    page.go()
    page.nav("Admin", "/admin")
    page.login(*credentials)
    page.visible(button("Cerrar Sesión"))


def test_WEB_01_brave_abre_visiontext_y_navega_por_menu(page):
    page.go()
    assert page.driver.execute_async_script(
        "const done = arguments[0]; navigator.brave?.isBrave().then(done, () => done(false)) ?? done(false);"
    ), "La sesión no corresponde a Brave"
    page.heading("Encuentra la imagen perfecta")
    page.nav("Imagen", "/image-search")
    page.heading("Búsqueda por Imagen")
    page.nav("Texto", "/text-search")
    page.heading("Encuentra la imagen perfecta")


def test_WEB_02_busqueda_textual_abre_el_original(page, evidence):
    page.go()
    assert not page.visible(page.SEARCH).is_enabled()
    page.fill(page.SEARCH_BOX, "   ")
    assert not page.visible(page.SEARCH).is_enabled()
    page.fill(page.SEARCH_BOX, "African elephant")
    page.click(page.SEARCH)
    stats = page.visible(page.STATS)
    assert re.match(r"Encontrados [1-9][0-9]* resultados", stats.text)
    thumbnail = page.picture((By.CSS_SELECTOR, 'img[alt^="african_elephant_"][src*="/api/thumbnails/"]'))
    thumbnail_path = urlsplit(thumbnail.get_attribute("src")).path
    label = thumbnail.get_attribute("alt")
    previous = set(page.driver.window_handles)
    main_tab = page.driver.current_window_handle
    page.click(named("h3", label))
    page.wait.until(lambda driver: len(driver.window_handles) == len(previous) + 1, "No se abrió el original")
    original_tab, = set(page.driver.window_handles) - previous
    try:
        page.driver.switch_to.window(original_tab)
        expected = thumbnail_path.replace("/api/thumbnails/", "/api/images/", 1)
        page.wait.until(lambda driver: urlsplit(driver.current_url).path == expected, expected)
        page.picture((By.CSS_SELECTOR, "body img"))
        evidence("original")
    finally:
        page.driver.close()
        page.driver.switch_to.window(main_tab)


def test_WEB_03_busqueda_por_imagen_recupera_archivo_conocido(page):
    page.go()
    page.nav("Imagen", "/image-search")
    page.file(page.IMAGE_INPUT, SAMPLE)
    page.picture(page.IMAGE_PREVIEW)
    page.click(button("Buscar Similares"))
    page.visible(named("h3", "Resultados Similares"))
    page.picture(matching_picture(SAMPLE.name))


def test_WEB_04_quitar_previsualizacion_y_rechazar_archivo_de_texto(page):
    page.go()
    page.nav("Imagen", "/image-search")
    page.file(page.IMAGE_INPUT, SAMPLE)
    page.picture(page.IMAGE_PREVIEW)
    page.click(page.IMAGE_REMOVE)
    page.visible(named("p", "La vista previa aparecerá aquí"))
    page.file(page.IMAGE_INPUT, INVALID)
    page.visible(named("p", "Por favor selecciona un archivo de imagen válido"))
    assert not page.driver.find_elements(*button("Buscar Similares"))
    assert not page.driver.find_elements(*page.IMAGE_PREVIEW)


def test_WEB_05_subida_y_catalogo_exigen_sesion(page):
    page.go()
    page.nav("Subir", "/upload")
    page.heading("Panel de Administración")
    page.visible(named("p", "Subir imágenes requiere una cuenta de administrador"))
    assert not page.driver.find_elements(*page.UPLOAD)
    page.go("/admin")
    page.visible(page.LOGIN_PASSWORD)
    assert not page.driver.find_elements(*page.TABLE)


def test_WEB_06_menu_en_ventana_estrecha(page):
    page.driver.set_window_size(470, 920)
    page.go()
    assert page.driver.execute_script("return window.innerWidth") < 768

    def toggle(driver):
        shown = [item for item in driver.find_elements(By.CSS_SELECTOR, "header button") if item.is_displayed()]
        return shown[0] if len(shown) == 1 else False

    page.wait.until(toggle, "Se esperaba el botón del menú móvil").click()
    choice = named("header//button", "Búsqueda por Imagen")
    page.click(choice)
    page.heading("Búsqueda por Imagen")
    assert urlsplit(page.driver.current_url).path == "/image-search"
    page.wait.until(EC.invisibility_of_element_located(choice))


def test_WEB_07_descarga_apk_o_aviso_de_disponibilidad(page, downloads):
    page.go()
    page.click(button("Descargar app (APK)"))
    if os.environ["VT_WEB_ENV"] == "local":
        notice = page.visible((By.CSS_SELECTOR, 'aside[aria-label="Aplicación Android"] [role="alert"]'))
        assert "requiere el almacenamiento de Drive" in notice.text
        assert not any(downloads.iterdir())
    else:
        notice = By.CSS_SELECTOR, 'aside[aria-label="Aplicación Android"] [role="status"]'
        page.wait.until(EC.text_to_be_present_in_element(notice, "APK enviada al navegador"))
        apk = downloads / "VisionText.apk"
        page.wait.until(lambda _: apk.is_file() and is_zipfile(apk), "No se descargó una APK válida")
        with ZipFile(apk) as package:
            assert {"AndroidManifest.xml", "classes.dex"} <= set(package.namelist())


def test_WEB_08_login_paginacion_recarga_y_cierre_de_sesion(page, credentials, evidence):
    open_admin(page, credentials)
    first = page.pager(1)
    assert len(first) == len(set(first)) == 30
    assert not page.visible(button("Anterior")).is_enabled()
    page.click(button("Siguiente"))
    second = page.pager(2, previous=first)
    assert 1 <= len(second) <= 30
    assert not set(first).intersection(second)
    evidence("pagina-2")
    page.click(button("Anterior"))
    assert page.pager(1, previous=second) == first
    page.driver.refresh()
    assert page.pager(1) == first
    page.click(button("Cerrar Sesión"))
    page.visible(page.LOGIN_PASSWORD)
    page.driver.refresh()
    page.visible(page.LOGIN_PASSWORD)
    assert not page.driver.find_elements(*page.TABLE)


@pytest.mark.solo_local
def test_WEB_09_login_incorrecto_muestra_error(page, credentials):
    page.go()
    page.nav("Admin", "/admin")
    page.login(credentials[0], uuid4().hex)
    page.visible(named("p", "Credenciales incorrectas"))
    assert not page.driver.find_elements(*page.TABLE)


@pytest.mark.solo_local
def test_WEB_10_subir_confirmar_y_borrar_imagen_temporal(page, credentials, tmp_path, evidence):
    photo = copy_sample(tmp_path)
    page.go()
    page.nav("Subir", "/upload")
    page.login(*credentials)
    page.heading("Subir Imágenes")
    page.file(page.UPLOAD, photo)
    page.picture((By.CSS_SELECTOR, f'img[alt="{photo.name}"][src^="blob:"]'))
    description = "a photo of an African elephant"
    page.fill(page.DESCRIPTION, description)
    page.click(button("Subir 1 imagen"))
    page.visible(named("h3", "Resultados de la subida"))
    message = (By.XPATH, f'//p[contains(normalize-space(.), "{photo.name}") and contains(., "subida exitosamente")]')
    page.visible(message)
    evidence("subida")
    page.nav("Admin", "/admin")
    page.picture(matching_picture(photo.name))
    row = page.visible(page.row(photo.name))
    assert description in row.text
    remove = By.XPATH, page.row(photo.name)[1] + '//button[normalize-space(.)="Eliminar"]'
    for action in ("Cancelar", "Eliminar"):
        page.click(remove)
        if action == "Eliminar":
            page.visible(page.CONFIRM)
            evidence("confirmacion")
        page.confirm(action)
    page.wait.until(lambda driver: driver.find_elements(*page.TABLE) and not driver.find_elements(*page.row(photo.name)),
                    "El catálogo no volvió a mostrarse sin la imagen de prueba")


@pytest.mark.solo_local
def test_WEB_11_subida_muestra_archivo_invalido_y_baja_similitud(page, credentials, tmp_path):
    page.go()
    page.nav("Subir", "/upload")
    page.login(*credentials)
    page.heading("Subir Imágenes")
    page.file(page.UPLOAD, INVALID)
    page.visible(named("p", "Algunos archivos no son imágenes válidas y fueron ignorados"))
    assert not page.driver.find_elements(*button("Subir 1 imagen"))
    photo = copy_sample(tmp_path)
    page.file(page.UPLOAD, photo)
    page.fill(page.DESCRIPTION, "a studio photo of a close-up of a computer microprocessor on a printed circuit board")
    page.click(button("Subir 1 imagen"))
    page.visible(named("h3", "Resultados de la subida"))
    page.visible((By.XPATH, '//p[starts-with(normalize-space(.), "Similitud insuficiente:")]'))
