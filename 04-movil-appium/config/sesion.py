import os
from pathlib import Path

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.client_config import AppiumClientConfig

SUITE = Path(__file__).resolve().parents[1]
PROJECT = SUITE.parents[1]
PACKAGE = "pe.visiontext.app"
DISTRIBUTION_APK = PROJECT / "VisionText-android" / "artifacts" / "VisionText.apk"
SAMPLE = PROJECT / "VisionText-backend" / "dataset_final" / "african_elephant_african_elephant-0005.jpg"


def apk_path():
    apk = Path(os.environ.get("VISIONTEXT_APK", DISTRIBUTION_APK)).resolve()
    if not apk.is_file():
        raise RuntimeError(f"APK no encontrada: {apk}")
    return apk


def open_session():
    udid = os.environ.get("VISIONTEXT_ANDROID_UDID")
    if not udid:
        raise RuntimeError("Configura VISIONTEXT_ANDROID_UDID con el ID que indica adb devices.")

    options = UiAutomator2Options().load_capabilities(
        {
            "platformName": "Android",
            "appium:automationName": "UiAutomator2",
            "appium:udid": udid,
            "appium:app": str(apk_path()),
            "appium:appPackage": PACKAGE,
            "appium:appActivity": ".MainActivity",
            "appium:uiautomator2ServerLaunchTimeout": 120_000,
            "appium:uiautomator2ServerInstallTimeout": 60_000,
            "appium:adbExecTimeout": 45_000,
            "appium:newCommandTimeout": 240,
            "appium:disableWindowAnimation": True,
        }
    )
    endpoint = os.environ.get("VISIONTEXT_APPIUM_URL", "http://127.0.0.1:4723")
    client = AppiumClientConfig(remote_server_addr=endpoint, timeout=240)
    return webdriver.Remote(options=options, client_config=client)
