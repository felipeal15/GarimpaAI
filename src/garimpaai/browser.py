import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

_driver = None


def create_driver(*, headless: bool = True) -> webdriver.Chrome:
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    )

    chrome_binary = os.environ.get("GARIMPA_CHROME_BINARY")
    if chrome_binary:
        options.binary_location = chrome_binary

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def get_driver(*, headless: bool = True) -> webdriver.Chrome:
    global _driver
    if _driver is None:
        _driver = create_driver(headless=headless)
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        try:
            _driver.quit()
        finally:
            _driver = None
