"""
1_open_browser.py
功能：開啟 Chrome 瀏覽器，前往 E等公務園首頁，回傳 driver 物件。
"""

import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def open_browser(headless: bool = config.HEADLESS) -> webdriver.Chrome:
    """
    建立並回傳 Chrome WebDriver，並前往 E等公務園首頁。

    Args:
        headless: True 表示不顯示瀏覽器視窗。

    Returns:
        已開啟的 webdriver.Chrome 物件。
    """
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    # 避免被網站偵測為自動化程式
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)

    # 隱藏 webdriver 特徵
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    log.info("✅ 瀏覽器已啟動")
    driver.get(config.BASE_URL)
    log.info(f"✅ 已前往：{config.BASE_URL}")

    return driver


# ── 單獨執行測試 ──────────────────────────
if __name__ == "__main__":
    driver = open_browser()
    input("瀏覽器已開啟，按 Enter 關閉...")
    driver.quit()
