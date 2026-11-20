"""Create a clean Selenium session using the Brave executable."""

import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

ROOT = Path(__file__).resolve().parent


def open_brave(downloads, visible=False):
    path = os.environ.get("BRAVE_BINARY", "")
    if Path(path).name.lower() != "brave.exe" or not Path(path).is_file():
        raise ValueError("Define BRAVE_BINARY con el brave.exe devuelto por Resolver-Brave.ps1.")
    os.environ.setdefault("SE_CACHE_PATH", str(ROOT / "target" / "selenium-manager"))
    os.environ.setdefault("SE_AVOID_STATS", "true")
    options = webdriver.ChromeOptions()
    options.binary_location = path
    if not visible:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1360,980")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_experimental_option("prefs", {
        "download.default_directory": str(downloads.resolve()),
        "download.prompt_for_download": False,
    })
    driver_path = os.environ.get("CHROMEDRIVER_PATH")
    service = Service(executable_path=driver_path) if driver_path else Service()
    driver = webdriver.Chrome(options=options, service=service)
    driver.set_page_load_timeout(45)
    driver.set_script_timeout(15)
    return driver
