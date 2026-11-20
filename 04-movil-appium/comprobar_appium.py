from pathlib import Path

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.sesion import open_session


def main():
    folder = Path(__file__).resolve().parent
    driver = open_session()
    try:
        wait = WebDriverWait(driver, 30)
        text_search = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Explora por texto")')
        image_tab = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Imagen").clickable(true)')
        image_search = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Explora por imagen")')
        wait.until(EC.visibility_of_element_located(text_search))
        wait.until(EC.element_to_be_clickable(image_tab)).click()
        wait.until(EC.visibility_of_element_located(image_search))
        screenshot = folder / "evidence" / "appium-navegacion.png"
        screenshot.parent.mkdir(exist_ok=True)
        if not driver.save_screenshot(str(screenshot)):
            raise RuntimeError(f"No se pudo guardar la captura: {screenshot}")
        print(f"Appium abrió VisionText y cambió a Imagen. Captura: {screenshot}")
    except TimeoutException:
        diagnostics = folder / "target"
        diagnostics.mkdir(exist_ok=True)
        (diagnostics / "pantalla-appium.xml").write_text(driver.page_source, encoding="utf-8")
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
