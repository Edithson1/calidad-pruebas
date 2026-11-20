import base64
import json
import os
from pathlib import Path

import pytest
from pytest_html import extras

from browser import open_brave
from pages.visiontext import VisionText


def pytest_collection_modifyitems(config, items):
    if os.environ.get("VT_WEB_ENV") != "local":
        excluded = [item for item in items if item.get_closest_marker("solo_local")]
        if excluded:
            items[:] = [item for item in items if item not in excluded]
            config.hook.pytest_deselected(items=excluded)


def pytest_html_report_title(report):
    report.title = f"VisionText · Selenium con Brave · {os.environ.get('VT_WEB_ENV', '')}"


@pytest.fixture
def downloads(tmp_path):
    folder = tmp_path / "downloads"
    folder.mkdir()
    return folder


@pytest.fixture
def driver(downloads):
    with open_brave(downloads, visible=os.environ.get("VT_WEB_VISIBLE") == "1") as session:
        folder = Path(os.environ["VT_WEB_REPORT_DIR"])
        metadata = folder / "navegador.json"
        if not metadata.exists():
            info = {
                "chromium": session.capabilities["browserVersion"],
                "chromedriver": session.capabilities["chrome"]["chromedriverVersion"].split(" ")[0],
                "visible": os.environ.get("VT_WEB_VISIBLE") == "1",
            }
            metadata.write_text(json.dumps(info, indent=2), encoding="utf-8")
        yield session


@pytest.fixture
def page(driver):
    environment = os.environ["VT_WEB_ENV"]
    return VisionText(driver, os.environ["VT_WEB_URL"], 90 if environment == "render" else 35)


@pytest.fixture
def credentials():
    return os.environ["VT_WEB_USER"], os.environ["VT_WEB_PASSWORD"]


def case_id(item):
    return "-".join(item.name.split("_", 3)[1:3])


def capture(driver, directory, case, label):
    folder = Path(directory) / "capturas"
    folder.mkdir(exist_ok=True)
    data = driver.get_screenshot_as_png()
    (folder / f"{case}-{label}.png").write_bytes(data)
    return extras.png(base64.b64encode(data).decode("ascii"), name=f"Captura {case} · {label}")


@pytest.fixture
def evidence(request, driver):
    def checkpoint(label):
        shot = capture(driver, os.environ["VT_WEB_REPORT_DIR"], case_id(request.node), label)
        request.node._visiontext_evidence.append(shot)

    request.node._visiontext_evidence = []
    return checkpoint


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    driver = item.funcargs.get("driver")
    directory = os.environ.get("VT_WEB_REPORT_DIR")
    if report.when == "call" and driver and directory:
        items = getattr(report, "extras", []) + getattr(item, "_visiontext_evidence", [])
        try:
            items.append(capture(driver, directory, case_id(item), report.outcome))
        except Exception:
            items.append(extras.text("La sesión no respondió al solicitar captura.", name="Evidencia"))
        report.extras = items
    return report
