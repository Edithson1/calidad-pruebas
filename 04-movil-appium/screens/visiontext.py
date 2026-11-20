from io import BytesIO
import json
import re

from appium.webdriver.common.appiumby import AppiumBy
from PIL import Image
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def selector(method, value, suffix=""):
    expression = f"new UiSelector().{method}({json.dumps(value, ensure_ascii=False)}){suffix}"
    return AppiumBy.ANDROID_UIAUTOMATOR, expression


def text(value):
    return selector("text", value)


def button(value):
    return selector("text", value, ".clickable(true)")


def access(value):
    return AppiumBy.ACCESSIBILITY_ID, value


class VisionText:
    POSITIVE = AppiumBy.ID, "android:id/button1"
    NEGATIVE = AppiumBy.ID, "android:id/button2"
    NEUTRAL = AppiumBy.ID, "android:id/button3"
    TILES = selector("descriptionStartsWith", "Abrir ")
    SCROLL = AppiumBy.CLASS_NAME, "android.widget.ScrollView"
    COUNTER = selector("textMatches", "[0-9]+ coincidencias · .*")
    TABS = {
        "Texto": "Explora por texto",
        "Imagen": "Explora por imagen",
        "Subir": "Sube imágenes",
        "Admin": "Gestiona la colección",
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 25, ignored_exceptions=(StaleElementReferenceException,))
        self.request = WebDriverWait(driver, 190, ignored_exceptions=(StaleElementReferenceException,))

    def wait_for_launch(self):
        return WebDriverWait(self.driver, 65).until(
            EC.visibility_of_element_located(text(self.TABS["Texto"])), "VisionText no terminó de iniciar"
        )

    def visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator), f"No se mostró {locator[1]}")

    def shown(self, locator):
        return next((item for item in self.driver.find_elements(*locator) if item.is_displayed()), None)

    def tap(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator), f"No se pudo tocar {locator[1]}").click()

    def go(self, tab):
        self.tap(button(tab))
        self.visible(text(self.TABS[tab]))

    def fill(self, label, value):
        field = self.visible(access(label))
        field.clear()
        if value:
            field.send_keys(value)
        if self.driver.is_keyboard_shown():
            self.driver.hide_keyboard()

    def swipe(self, direction="up"):
        scroll = self.visible(self.SCROLL)
        self.driver.execute_script(
            "mobile: swipeGesture", {"elementId": scroll.id, "direction": direction, "percent": 0.65}
        )

    def reveal(self, locator, steps=8):
        scroll = self.visible(self.SCROLL)
        for _ in range(steps):
            found = self.shown(locator)
            if found:
                return found
            can_continue = self.driver.execute_script(
                "mobile: scrollGesture",
                {"elementId": scroll.id, "direction": "down", "percent": 0.35, "speed": 1800},
            )
            if not can_continue:
                break
        return self.visible(locator)

    def result_count(self):
        counter = self.request.until(EC.visibility_of_element_located(self.COUNTER), "No llegaron resultados")
        return int(counter.text.split()[0])

    def cards(self):
        return {
            item.get_attribute("content-desc"): item.rect["y"]
            for item in self.driver.find_elements(*self.TILES)
            if item.is_displayed()
        }

    def open_original(self, description):
        self.tap(access(description))
        name = description.removeprefix("Abrir ")
        self.visible(text(name))
        self.request.until(lambda _: self.picture_loaded(access(name)), f"No cargó el original {name}")
        return name

    def picture_loaded(self, locator):
        image = self.shown(locator)
        if not image:
            return False
        rect = image.rect
        with Image.open(BytesIO(self.driver.get_screenshot_as_png())) as screen:
            x, y, width, height = (rect[key] for key in ("x", "y", "width", "height"))
            area = screen.crop((x + width // 5, y + height // 5, x + 4 * width // 5, y + 4 * height // 5))
            palette = area.convert("RGB").resize((36, 36)).quantize(colors=24)
            return len(palette.getcolors()) >= 12

    def field_has_error(self, label):
        rect = self.visible(access(label)).rect
        x, y, width, height = (rect[key] for key in ("x", "y", "width", "height"))
        with Image.open(BytesIO(self.driver.get_screenshot_as_png())) as screen:
            bounds = (x + 4 * width // 5, y + height // 5, x + width, y + 4 * height // 5)
            corner = screen.crop(bounds).convert("RGB").resize((50, 30))
            return sum(red > 220 and green < 60 and blue < 120 for red, green, blue in corner.get_flattened_data()) >= 30

    def choose_photo(self, control, filename):
        self.tap(button(control))
        photo = text(filename)
        tile = selector("descriptionStartsWith", filename + ",")
        roots = access("Show roots")
        choice = self.wait.until(
            lambda _: self.shown(tile) or self.shown(photo) or self.shown(roots),
            "No abrió el selector de Android",
        )
        if choice.get_attribute("content-desc") == "Show roots":
            choice.click()
            self.tap(text("Downloads"))
            choice = self.wait.until(lambda _: self.shown(tile) or self.shown(photo), f"No se encontró {filename}")
        choice.click()
        self.visible(text(filename))

    def configure_server(self, url):
        self.tap(button("Servidor"))
        self.fill("URL del backend", url)
        self.tap(self.POSITIVE)
        self.wait.until(EC.invisibility_of_element_located(text("Servidor de VisionText")))

    def submit_login(self, user, password):
        self.fill("Usuario", user)
        self.fill("Contraseña", password)
        self.tap(button("Iniciar sesión"))

    def wait_for_catalog(self, expected=None):
        locator = (
            text(f"Imágenes guardadas · {expected}") if expected is not None
            else selector("textStartsWith", "Imágenes guardadas · ")
        )
        item = self.request.until(EC.visibility_of_element_located(locator), "No se mostró el catálogo")
        return int(item.text.rsplit(" ", 1)[-1])

    def page_indicator(self, number):
        locator = selector("textMatches", rf"{number} / [1-9][0-9]*")
        self.request.until(EC.visibility_of_element_located(locator), f"No abrió la página {number}")

    def delete_button(self, filename):
        assert re.fullmatch(r"[a-z0-9-]+\.jpg", filename)
        return AppiumBy.XPATH, f'//*[@content-desc="Abrir {filename}"]/../*[@text="Eliminar"]'
