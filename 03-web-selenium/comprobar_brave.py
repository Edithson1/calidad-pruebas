from pathlib import Path
from tempfile import TemporaryDirectory

from browser import open_brave


def main():
    with TemporaryDirectory() as downloads, open_brave(Path(downloads)) as driver:
        driver.get("brave://version")
        assert "brave.exe" in driver.find_element("tag name", "body").text.lower()
        caps = driver.capabilities
        print("Brave Chromium:", caps["browserVersion"])
        print("ChromeDriver:", caps.get("chrome", {}).get("chromedriverVersion", "").split(" ")[0])


if __name__ == "__main__":
    main()
