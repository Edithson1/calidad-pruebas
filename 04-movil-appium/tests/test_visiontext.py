import pytest
from selenium.webdriver.support import expected_conditions as EC

from config.sesion import PACKAGE
from screens.visiontext import access, button, selector, text


def test_APP_01_navegacion_nativa_en_las_cuatro_pestanas(app, evidence):
    assert app.driver.current_package == PACKAGE
    assert app.driver.current_context == "NATIVE_APP"
    for tab in ("Imagen", "Subir", "Admin", "Texto"):
        app.go(tab)
        assert app.visible(button(tab)).get_attribute("selected") == "true"
        if tab == "Imagen":
            evidence("tap-imagen")


def test_APP_02_busqueda_vacia_muestra_validacion(app):
    app.fill("Ej. Una ciudad de noche", "   ")
    app.tap(button("Buscar imágenes"))
    app.reveal(text("Escribe una descripción para buscar."))
    assert app.shown(text("Resultados")) is None


def test_APP_03_busqueda_textual_desliza_y_abre_original(app, catalog, evidence):
    app.fill("Ej. Una ciudad de noche", "African elephant")
    app.tap(button("Buscar imágenes"))
    assert app.result_count() >= 4, "Se requiere una lista desplazable de coincidencias"
    app.reveal(app.TILES)
    before = app.cards()
    evidence("resultados-antes-del-swipe")
    app.swipe("up")
    after = app.wait.until(lambda _: app.cards() != before and app.cards(), "El gesto no cambió la lista visible")
    assert any(label not in before or after[label] < before[label] for label in after)
    evidence("resultados-despues-del-swipe")

    matching = selector("descriptionStartsWith", "Abrir african_elephant_")
    preview = app.reveal(matching)
    name = app.open_original(preview.get_attribute("content-desc"))
    assert name.startswith("african_elephant_")
    evidence("original-cargado")
    app.tap(app.POSITIVE)
    app.wait.until(EC.invisibility_of_element_located(app.POSITIVE))
    assert app.cards(), "La lista desapareció al cerrar la imagen"


def test_APP_04_busqueda_visual_recupera_la_foto_del_catalogo(app, catalog, sample_photo, evidence):
    app.go("Imagen")
    app.choose_photo("Seleccionar imagen", sample_photo)
    app.wait.until(lambda _: app.picture_loaded(access("Vista previa de la imagen seleccionada")))
    evidence("vista-previa")
    app.tap(button("Buscar similares"))
    assert app.result_count() > 0
    result = access(f"Abrir {sample_photo}")
    app.reveal(result)
    assert app.open_original(f"Abrir {sample_photo}") == sample_photo
    evidence("coincidencia-exacta")
    app.tap(app.POSITIVE)


def test_APP_05_cancelar_y_quitar_documento(app, sample_photo):
    app.go("Imagen")
    app.tap(button("Seleccionar imagen"))
    app.wait.until(lambda driver: driver.current_package.endswith(".documentsui"))
    app.driver.back()
    app.visible(button("Seleccionar imagen"))
    app.choose_photo("Seleccionar imagen", sample_photo)
    app.tap(button("Quitar imagen"))
    app.visible(button("Seleccionar imagen"))
    assert app.shown(text(sample_photo)) is None
    assert app.shown(button("Buscar similares")) is None


def test_APP_06_subida_y_admin_requieren_autenticacion(app):
    app.go("Subir")
    app.visible(text("Acceso de administrador"))
    app.visible(access("Contraseña"))
    assert app.shown(button("Seleccionar imágenes")) is None

    app.go("Admin")
    assert not app.field_has_error("Contraseña")
    app.tap(button("Iniciar sesión"))
    app.wait.until(lambda _: app.field_has_error("Contraseña"), "No se marcó la contraseña como obligatoria")
    assert app.shown(button("Actualizar")) is None


def test_APP_07_servidor_rechaza_url_invalida_y_conserva_la_configuracion(app, evidence):
    app.tap(button("Servidor"))
    original = app.visible(access("URL del backend")).text
    app.fill("URL del backend", "no-es-una-url")
    assert not app.field_has_error("URL del backend")
    app.tap(app.POSITIVE)
    app.wait.until(lambda _: app.field_has_error("URL del backend"), "No se marcó la URL como inválida")
    evidence("url-invalida")
    app.tap(app.NEGATIVE)
    app.tap(button("Servidor"))
    assert app.visible(access("URL del backend")).text == original
    app.tap(app.NEGATIVE)


def test_APP_08_probar_servidor_y_persistir_el_ajuste(fresh_app, environment, server_url, evidence):
    if environment == "local":
        updated = server_url.replace("127.0.0.1", "10.0.2.2")
    else:
        updated = server_url + ":443"
    fresh_app.tap(button("Servidor"))
    assert fresh_app.visible(access("URL del backend")).text != updated
    fresh_app.fill("URL del backend", updated + "/")
    fresh_app.tap(fresh_app.NEUTRAL)
    fresh_app.request.until(EC.visibility_of_element_located(text("API accesible · healthy")))
    evidence("api-accesible")
    fresh_app.tap(fresh_app.POSITIVE)
    fresh_app.driver.terminate_app(PACKAGE)
    fresh_app.driver.activate_app(PACKAGE)
    fresh_app.wait_for_launch()
    fresh_app.tap(button("Servidor"))
    assert fresh_app.visible(access("URL del backend")).text == updated
    fresh_app.tap(fresh_app.NEGATIVE)


def test_APP_09_login_catalogo_y_logout(app, catalog, credentials, evidence):
    app.go("Admin")
    app.submit_login(*credentials)
    count = app.wait_for_catalog()
    assert count > 0
    if count > 30:
        app.page_indicator(1)
        assert not app.visible(button("Anterior")).is_enabled()
        app.tap(button("Siguiente"))
        app.page_indicator(2)
        evidence("catalogo-pagina-dos")
        app.tap(button("Anterior"))
        app.page_indicator(1)
    else:
        evidence("catalogo")

    app.go("Subir")
    app.visible(button("Seleccionar imágenes"))
    app.go("Admin")
    app.tap(button("Cerrar sesión"))
    app.visible(text("Acceso de administrador"))
    app.go("Subir")
    assert app.shown(button("Seleccionar imágenes")) is None


@pytest.mark.solo_local
def test_APP_10_credenciales_incorrectas_muestran_error(app, credentials):
    app.go("Admin")
    app.submit_login(credentials[0], "contrasena-prueba-incorrecta")
    app.request.until(EC.visibility_of_element_located(text("Credenciales incorrectas")))
    assert app.shown(button("Actualizar")) is None
    assert app.visible(button("Iniciar sesión")).is_enabled()


@pytest.mark.solo_local
def test_APP_11_sube_y_elimina_solo_la_imagen_temporal(app, catalog, credentials, upload_photo, evidence):
    before = catalog()
    app.go("Subir")
    app.submit_login(*credentials)
    app.choose_photo("Seleccionar imágenes", upload_photo)
    app.reveal(access("Descripción opcional"))
    app.fill("Descripción opcional", "a photo of an African elephant")
    app.swipe("down")
    app.tap(button("Subir 1 imagen"))
    app.request.until(EC.visibility_of_element_located(selector("textContains", "subida exitosamente")))
    assert catalog() == before + 1
    evidence("subida-confirmada")

    app.go("Admin")
    app.wait_for_catalog(expected=before + 1)
    deletion = app.delete_button(upload_photo)
    app.reveal(deletion)
    app.tap(deletion)
    app.visible(text(f"Se eliminará {upload_photo} de la colección."))
    app.tap(app.NEGATIVE)
    assert catalog() == before + 1
    app.tap(deletion)
    app.visible(text("Eliminar imagen"))
    evidence("confirmacion-eliminar")
    app.tap(app.POSITIVE)
    app.wait_for_catalog(expected=before)
    assert catalog() == before
    assert app.shown(access(f"Abrir {upload_photo}")) is None
