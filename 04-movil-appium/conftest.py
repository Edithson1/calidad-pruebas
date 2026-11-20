import base64
from hashlib import file_digest
import json
import os
from pathlib import Path
import re
from uuid import uuid4

from dotenv import dotenv_values
import pytest
from pytest_html import extras
import requests

from config.sesion import PACKAGE, PROJECT, SAMPLE, apk_path, open_session
from screens.visiontext import VisionText

RENDER = "https://visiontext-backend.onrender.com"


def pytest_html_report_title(report):
    report.title = f"VisionText Android · Appium · {os.environ['VT_APP_ENV']}"


@pytest.fixture(scope="session")
def environment():
    return os.environ["VT_APP_ENV"]


@pytest.fixture(scope="session")
def server_url(environment):
    if environment == "render":
        return RENDER
    if os.environ.get("VT_KARATE_LOCAL_ISOLATED") != "1":
        pytest.fail("El perfil local requiere la instancia temporal de Ejecutar-Local.ps1.")
    return os.environ["VT_KARATE_URL"]


@pytest.fixture(scope="session")
def credentials(environment):
    if environment == "local":
        return os.environ["VT_KARATE_ADMIN_USER"], os.environ["VT_KARATE_ADMIN_PASSWORD"]
    config = dotenv_values(PROJECT / "VisionText-backend" / ".env.render", interpolate=False)
    user = os.environ.get("VT_APP_USER") or config.get("ADMIN_USERNAME")
    password = os.environ.get("VT_APP_PASSWORD") or config.get("ADMIN_PASSWORD")
    if not (user and password):
        pytest.skip("Credenciales de administrador desplegado sin configurar.")
    return user, password


@pytest.fixture(scope="session")
def catalog(server_url, environment, request):
    def count():
        response = requests.get(f"{server_url}/api/health", timeout=(10, 60))
        response.raise_for_status()
        report = response.json()
        assert report["status"] == "healthy", "El backend no está listo"
        assert report["images_in_db"] == report["vectors_in_index"], "El catálogo y el índice están desincronizados"
        return report["images_in_db"]

    if environment == "local":
        assert count() == 0, "El catálogo temporal debe empezar vacío"
        user, password = request.getfixturevalue("credentials")
        response = requests.post(
            f"{server_url}/api/admin/login", data={"username": user, "password": password}, timeout=15
        )
        response.raise_for_status()
        headers = {"Authorization": "Bearer " + response.json()["access_token"]}
        samples = sorted(SAMPLE.parent.glob("african_elephant_*.jpg"))[:8]
        samples += sorted(SAMPLE.parent.glob("zebra_*.jpg"))[:4]
        assert len(samples) == 12 and SAMPLE in samples, "Faltan imágenes para sembrar el catálogo"
        for image in samples:
            with image.open("rb") as content:
                result = requests.post(
                    f"{server_url}/api/upload", headers=headers,
                    files={"image": (image.name, content, "image/jpeg")}, timeout=60
                )
            assert result.ok and result.json().get("success"), f"No se preparó {image.name} (HTTP {result.status_code})"
        assert count() == len(samples), "La preparación no indexó todas las imágenes"
    return count


@pytest.fixture(scope="session")
def driver(environment, server_url):
    udid = os.environ.get("VISIONTEXT_ANDROID_UDID", "")
    if not re.fullmatch(r"emulator-[0-9]+", udid):
        pytest.fail("Ejecuta la suite en el emulador dedicado desde Ejecutar-Appium.ps1.")

    session = open_session()
    try:
        session.update_settings({"waitForIdleTimeout": 1000, "waitForSelectorTimeout": 0})
        report = Path(os.environ["VT_APP_REPORT_DIR"])
        with apk_path().open("rb") as apk:
            checksum = file_digest(apk, "sha256").hexdigest()
        metadata = {
            "entorno": environment,
            "backend": server_url,
            "apk": apk_path().name,
            "sha256": checksum,
            "emulador": os.environ["VT_APP_AVD"],
            "dispositivo": udid,
            "android": session.capabilities.get("platformVersion"),
            "motor": "UiAutomator2",
            "paquete": PACKAGE,
        }
        (report / "entorno.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        yield session
    finally:
        session.quit()


@pytest.fixture
def fresh_app(driver):
    driver.terminate_app(PACKAGE, timeout=10_000)
    driver.execute_script("mobile: clearApp", {"appId": PACKAGE})
    driver.activate_app(PACKAGE)
    page = VisionText(driver)
    page.wait_for_launch()
    return page


@pytest.fixture
def app(fresh_app, environment, server_url):
    if environment == "local":
        fresh_app.configure_server(server_url.replace("127.0.0.1", "10.0.2.2"))
    return fresh_app


@pytest.fixture(scope="session")
def sample_photo(driver):
    driver.push_file(f"/sdcard/Download/{SAMPLE.name}", source_path=str(SAMPLE))
    return SAMPLE.name


@pytest.fixture
def upload_photo(driver):
    name = f"appium-{uuid4().hex}.jpg"
    driver.push_file(f"/sdcard/Download/{name}", source_path=str(SAMPLE))
    return name


def case_id(item):
    return "-".join(item.name.split("_", 3)[1:3])


def capture(driver, directory, case, label):
    folder = Path(directory) / "capturas"
    folder.mkdir(exist_ok=True)
    data = driver.get_screenshot_as_png()
    (folder / f"{case}-{label}.png").write_bytes(data)
    return extras.png(base64.b64encode(data).decode("ascii"), name=f"{case} · {label}")


@pytest.fixture
def evidence(request, driver):
    request.node.appium_evidence = []

    def checkpoint(label):
        request.node.appium_evidence.append(
            capture(driver, os.environ["VT_APP_REPORT_DIR"], case_id(request.node), label)
        )

    return checkpoint


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    driver = item.funcargs.get("driver") or getattr(item.funcargs.get("app"), "driver", None)
    directory = os.environ.get("VT_APP_REPORT_DIR")
    if (report.when == "call" or report.when == "setup" and report.failed) and driver and directory:
        items = getattr(report, "extras", []) + getattr(item, "appium_evidence", [])
        try:
            items.append(capture(driver, directory, case_id(item), report.outcome))
        except Exception as error:
            items.append(extras.text(f"No se pudo obtener captura ({type(error).__name__}).", name="Evidencia"))
        report.extras = items
    return report
