"""
6_fill_questionnaire.py
功能：防閒置迴圈結束後，自動填寫課程問卷/評價。
  Step 1. 在 frame 內點擊「問卷/評價」
  Step 2. 在 frame 內點擊「填寫問卷」（會開啟新視窗1）
  Step 3. 切換至新視窗1，勾選/選取所有題目選項
  Step 4. 點擊「確定繳交」
  Step 5. 處理確認對話框（視窗2：您確定要繳交嗎？）→ 點「確定」
  Step 6. 關閉所有額外分頁，切回主視窗，繼續下一門課
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    UnexpectedAlertPresentException,
)

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

QUESTIONNAIRE_ANSWERS = [
    {
        "name": "ans[WM_ITEM1_1000100000_10001_1577345794_709552][ANS01][]",
        "value": "6",
        "type": "checkbox",
    },
    {
        "name": "ans[WM_ITEM1_1000100000_10001_1577345888_580017][ANS01]",
        "value": "5",
        "type": "radio",
    },
    {
        "name": "ans[WM_ITEM1_1000100000_10001_1577345937_932652][ANS01]",
        "value": "5",
        "type": "radio",
    },
    {
        "name": "ans[WM_ITEM1_1000100000_10001_1577345989_934916][ANS01]",
        "value": "5",
        "type": "radio",
    },
]


def fill_questionnaire(driver: webdriver.Chrome) -> bool:
    main_window = driver.current_window_handle

    log.info("── 問卷 Step 1：點擊「問卷/評價」")
    clicked = _click_in_frames(
        driver,
        selectors=[
            "#SYS_04_02_003",
            "a[href*='questionnaire_list.php']",
            "a[target='s_main'][href*='questionnaire']",
        ],
        desc="問卷/評價",
    )
    if not clicked:
        log.warning("⚠️  找不到「問卷/評價」連結，可能此課程無問卷，跳過")
        return False

    log.info("── 問卷 Step 2：點擊「填寫問卷」")
    existing_windows = set(driver.window_handles)
    filled = _click_in_frames(
        driver,
        selectors=[
            "div.main-text",
            "a[href*='questionnaire']",
        ],
        desc="填寫問卷",
        text_filter="填寫問卷",
    )
    if not filled:
        log.warning("⚠️  找不到「填寫問卷」按鈕，可能問卷尚未開放或已填寫")
        return False

    log.info("── 問卷 Step 3：切換至問卷視窗並填答")
    try:
        wait = WebDriverWait(driver, 15)
        wait.until(lambda d: len(d.window_handles) > len(existing_windows))
        new_windows = set(driver.window_handles) - existing_windows
        questionnaire_window = new_windows.pop()
        driver.switch_to.window(questionnaire_window)
        log.info(f"✅ 已切換至問卷視窗：{driver.title}")
        time.sleep(2)
    except TimeoutException:
        log.error("❌ 等待問卷視窗逾時，未偵測到新視窗")
        return False

    success = _answer_questions(driver)
    if not success:
        log.warning("⚠️  部分題目未能作答，仍嘗試繳交")

    log.info("── 問卷 Step 4：點擊「確定繳交」")
    try:
        submit_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[type='submit'][value='確定繳交'], "
                                  "input.cssBtn[value='確定繳交']")
            )
        )
        submit_btn.click()
        log.info("✅ 已點擊「確定繳交」")
        time.sleep(1)
    except TimeoutException:
        log.error("❌ 找不到「確定繳交」按鈕")
        driver.close()
        driver.switch_to.window(main_window)
        return False

    log.info("── 問卷 Step 5：確認繳交對話框")
    try:
        WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        log.info(f"✅ 偵測到對話框：「{alert.text}」→ 點擊確定")
        alert.accept()
        log.info("✅ 已點擊確定，等待視窗自動關閉...")
        time.sleep(2)
    except TimeoutException:
        log.warning("⚠️  未偵測到確認對話框，可能已自動處理")
    except UnexpectedAlertPresentException:
        try:
            alert = driver.switch_to.alert
            alert.accept()
            time.sleep(2)
        except Exception:
            pass

    log.info("── 問卷 Step 6：關閉所有額外分頁，切回主視窗")
    # 關閉所有非主視窗的分頁
    for handle in list(driver.window_handles):
        if handle != main_window:
            try:
                driver.switch_to.window(handle)
                driver.close()
                log.info(f"✅ 已關閉額外分頁：{handle}")
            except Exception as e:
                log.warning(f"關閉分頁 {handle} 時發生錯誤：{e}")

    try:
        driver.switch_to.window(main_window)
        log.info("✅ 已切回主視窗，繼續下一門課程")
    except Exception as e:
        try:
            driver.switch_to.window(driver.window_handles[0])
            log.warning(f"主視窗切換失敗，改用第一個視窗：{e}")
        except Exception as e2:
            log.error(f"無法切回任何視窗：{e2}")

    log.info("✅ 問卷填寫流程完成")
    return True


def _answer_questions(driver: webdriver.Chrome) -> bool:
    all_ok = True
    for i, q in enumerate(QUESTIONNAIRE_ANSWERS):
        name  = q["name"]
        value = q["value"]
        qtype = q["type"]
        try:
            selector = f"input[name='{name}'][value='{value}']"
            el = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            driver.execute_script("arguments[0].click();", el)
            log.info(f"✅ 第{i+1}題 {qtype} value={value} 勾選完成")
        except TimeoutException:
            log.warning(f"⚠️  第{i+1}題找不到元素：name=...{name[-20:]} value={value}")
            all_ok = False
        except Exception as e:
            log.warning(f"⚠️  第{i+1}題作答時發生錯誤：{e}")
            all_ok = False
        if i < len(QUESTIONNAIRE_ANSWERS) - 1:
            time.sleep(1)
    return all_ok


def _click_in_frames(
    driver: webdriver.Chrome,
    selectors: list,
    desc: str,
    text_filter: str = "",
) -> bool:
    try:
        frames = driver.find_elements(By.CSS_SELECTOR, "frame, iframe")
    except Exception:
        return False

    for frame in frames:
        try:
            driver.switch_to.frame(frame)
            for selector in selectors:
                try:
                    by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
                    elements = driver.find_elements(by, selector)
                    for el in elements:
                        text = el.text or ""
                        if text_filter and text_filter not in text:
                            continue
                        el.click()
                        log.info(f"✅ 在 frame 內點擊「{desc}」成功")
                        time.sleep(1.5)
                        driver.switch_to.default_content()
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        finally:
            try:
                driver.switch_to.default_content()
            except Exception:
                pass

    return False


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from open_browser import open_browser
    from login import login

    driver = open_browser()
    driver.get(config.BASE_URL)
    if login(driver):
        result = fill_questionnaire(driver)
        print(f"\n問卷填寫結果：{'✅ 成功' if result else '❌ 失敗或無問卷'}")
        input("按 Enter 關閉...")
    driver.quit()