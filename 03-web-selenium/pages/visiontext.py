"""Locators and actions shared by the VisionText browser scenarios."""

from pathlib import Path
from urllib.parse import urlsplit

from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def named(tag, text):
    return By.XPATH, f'//{tag}[normalize-space(.)="{text}"]'


def button(text):
    return named("button", text)


class VisionText:
    SEARCH_BOX = (By.CSS_SELECTOR, 'form input[placeholder^="Ej:"]')
    SEARCH = (By.CSS_SELECTOR, 'form button[type="submit"]')
    IMAGE_INPUT = (By.ID, "image-upload")
    IMAGE_PREVIEW = (By.CSS_SELECTOR, 'img[alt="Preview"]')
    IMAGE_REMOVE = (By.CSS_SELECTOR, 'button[title="Eliminar imagen"]')
    STATS = (By.XPATH, "//p[starts-with(normalize-space(.), 'Encontrados ')]")
    LOGIN_USER = (By.CSS_SELECTOR, 'main form:has(input[type="password"]) input[type="text"]')
    LOGIN_PASSWORD = (By.CSS_SELECTOR, 'main form input[type="password"]')
    TABLE = (By.CSS_SELECTOR, "main table")
    ROWS = (By.CSS_SELECTOR, "main table tbody tr")
    UPLOAD = (By.ID, "file-upload")
    DESCRIPTION = (By.CSS_SELECTOR, "textarea[placeholder]")
    PAGINATION = (By.CSS_SELECTOR, 'nav[aria-label="Paginación de imágenes"] [aria-live="polite"]')
    CONFIRM = (By.XPATH, '//h3[normalize-space(.)="Confirmar Eliminación"]/parent::div')

    def __init__(self, driver, url, seconds):
        self.driver = driver
        self.url = url.rstrip("/")
        self.wait = WebDriverWait(driver, seconds, poll_frequency=0.25,
                                  ignored_exceptions=(StaleElementReferenceException,))

    def go(self, path="/"):
        self.driver.get(self.url + path)
        self.visible(named("h1", "VisionText AI"))

    def visible(self, locator, message=""):
        return self.wait.until(EC.visibility_of_element_located(locator), message or str(locator))

    def click(self, locator):
        def click_when_ready(driver):
            node = EC.element_to_be_clickable(locator)(driver)
            if not node:
                return False
            driver.execute_script("arguments[0].scrollIntoView({block:'center',behavior:'instant'})", node)
            try:
                node.click()
            except ElementClickInterceptedException:
                return False
            return True

        self.wait.until(click_when_ready, f"No se pudo pulsar {locator}")

    def nav(self, label, path):
        self.click(named("header//button", label))
        self.wait.until(lambda driver: urlsplit(driver.current_url).path == path, path)

    def heading(self, text):
        return self.visible(named("h2", text))

    def fill(self, locator, value):
        def fill_when_ready(driver):
            node = EC.element_to_be_clickable(locator)(driver)
            if not node:
                return False
            node.clear()
            node.send_keys(value)
            return node.get_property("value") == value

        self.wait.until(fill_when_ready, f"No se pudo rellenar {locator}")

    def file(self, locator, path):
        self.wait.until(EC.presence_of_element_located(locator)).send_keys(str(Path(path).resolve()))

    def picture(self, locator):
        image = self.visible(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'})", image)
        return self.wait.until(lambda driver: self.loaded_picture(driver, locator), str(locator))

    @staticmethod
    def loaded_picture(driver, locator):
        node = driver.find_element(*locator)
        return node if node.is_displayed() and node.get_property("complete") and node.get_property("naturalWidth") else False

    def login(self, username, password):
        self.heading("Panel de Administración")
        self.fill(self.LOGIN_USER, username)
        self.fill(self.LOGIN_PASSWORD, password)
        self.click(button("Iniciar Sesión"))

    def pager(self, number, previous=()):
        self.wait.until(EC.text_to_be_present_in_element(self.PAGINATION, f"Página {number} de "))
        self.visible(self.TABLE)
        def current_rows(driver):
            ids = [element.text for element in driver.find_elements(By.CSS_SELECTOR, "main table tbody tr code")
                   if element.is_displayed()]
            return ids if ids and set(ids).isdisjoint(previous) else False

        return self.wait.until(current_rows, "No apareció la página de registros esperada")

    @staticmethod
    def row(filename):
        return By.XPATH, f'//main//table//tr[.//img[@alt="{filename}"]]'

    def confirm(self, action):
        dialog = self.visible(self.CONFIRM)
        dialog.find_element(By.XPATH, f'.//button[normalize-space(.)="{action}"]').click()
        self.wait.until(EC.invisibility_of_element_located(self.CONFIRM), "El cuadro de confirmación sigue abierto")
