# """
# 3_find_and_start_course.py
# 功能：登入後依序完成以下流程：
#   Step 1. 點擊「個人專區」
#   Step 2. 點擊「學習中課程」tab（title 不固定）
#   Step 3. 偵測課程圖片數量，依序進入每門課程
#   Step 4. 點擊「上課去」按鈕
#   Step 5. 在 s_catalog frame 中點選第二個（非第一個）選項開始上課
# """

# import time
# import logging
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import (
#     TimeoutException,
#     NoSuchElementException,
#     StaleElementReferenceException,
# )

# import config
# import threading
# from anti_idle import run_anti_idle_loop

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
# )
# log = logging.getLogger(__name__)

# PERSONAL_AREA_URL = "https://elearn.hrd.gov.tw/mooc/user/learn_dashboard.php"


# def _click(wait: WebDriverWait, by, selector: str, desc: str) -> bool:
#     """等待元素可點擊後點擊，成功回傳 True，逾時回傳 False。"""
#     try:
#         el = wait.until(EC.element_to_be_clickable((by, selector)))
#         el.click()
#         log.info(f"✅ {desc}")
#         time.sleep(1.5)
#         return True
#     except TimeoutException:
#         log.error(f"❌ 逾時找不到：{desc}（selector: {selector}）")
#         return False


# def find_and_start_course(
#     driver: webdriver.Chrome,
#     stop_flag: list = None,
# ) -> bool:
#     """
#     從個人專區找出所有學習中課程，依序進入並開始上課。
#     進入課程後會在背景啟動防閒置迴圈，可透過 stop_flag[0] = True 中止。

#     Args:
#         stop_flag: 傳入 [False]，設為 True 時停止防閒置迴圈；留空則自動建立。

#     Returns:
#         True 表示至少成功進入一門課程，False 表示失敗。
#     """
#     if stop_flag is None:
#         stop_flag = [False]
#     wait = WebDriverWait(driver, config.PAGE_LOAD_TIMEOUT)

#     # ── Step 1：點擊「個人專區」 ─────────────────────────────────────
#     log.info("── Step 1：點擊「個人專區」")
#     if not _click(
#         wait,
#         By.CSS_SELECTOR,
#         "a[href*='learn_dashboard.php'][title='個人專區']",
#         "已點擊「個人專區」",
#     ):
#         driver.save_screenshot("step1_personal_failed.png")
#         return False

#     # ── Step 2：點擊「學習中課程」tab ────────────────────────────────
#     # href="/mooc/user/learn_dashboard.php?tab=1"，title 值不固定
#     log.info("── Step 2：點擊學習中課程 tab")
#     if not _click(
#         wait,
#         By.CSS_SELECTOR,
#         "a[href*='learn_dashboard.php?tab=1']",
#         "已點擊學習中課程 tab",
#     ):
#         driver.save_screenshot("step2_tab_failed.png")
#         return False

#     # ── Step 3：偵測課程圖片，取得課程數量 ──────────────────────────
#     log.info("── Step 3：偵測課程圖片數量")
#     try:
#         wait.until(
#             EC.presence_of_element_located(
#                 (By.CSS_SELECTOR, "img[alt='課程代表圖']")
#             )
#         )
#         course_imgs = driver.find_elements(
#             By.CSS_SELECTOR, "img[alt='課程代表圖']"
#         )
#         total = len(course_imgs)
#         log.info(f"共找到 {total} 門課程")
#     except TimeoutException:
#         log.error("❌ 找不到任何課程圖片，請確認已有報名中的課程")
#         driver.save_screenshot("step3_no_course.png")
#         return False

#     if total == 0:
#         log.error("❌ 課程圖片數量為 0")
#         return False

#     # ── 依序處理每門課程 ─────────────────────────────────────────────
#     for i in range(total):
#         log.info(f"\n{'='*40}")
#         log.info(f"處理第 {i+1} / {total} 門課程")
#         log.info(f"{'='*40}")

#         success = _process_single_course(driver, wait, i, total, stop_flag)
#         if not success:
#             log.warning(f"第 {i+1} 門課程處理失敗，繼續下一門")

#         # 處理完一門後回到課程清單
#         if i < total - 1:
#             log.info("返回課程列表...")
#             driver.get(PERSONAL_AREA_URL + "?tab=1")
#             time.sleep(2)
#             # 重新等待課程圖片載入
#             try:
#                 wait.until(
#                     EC.presence_of_element_located(
#                         (By.CSS_SELECTOR, "img[alt='課程代表圖']")
#                     )
#                 )
#             except TimeoutException:
#                 log.warning("返回後找不到課程圖片")

#     log.info("✅ 所有課程處理完畢")
#     return True


# def _process_single_course(
#     driver: webdriver.Chrome,
#     wait: WebDriverWait,
#     index: int,
#     total: int,
#     stop_flag: list = None,
# ) -> bool:
#     """
#     處理單一課程：點圖進入 → 點「上課去」→ 啟動防閒置。

#     Args:
#         index:     第幾門課（從 0 開始）
#         total:     課程總數
#         stop_flag: 防閒置迴圈的停止旗標，傳入 [False] 可從外部中止。
#     """
#     if stop_flag is None:
#         stop_flag = [False]
#     # ── Step 3-a：點擊第 index 張課程圖片 ────────────────────────────
#     try:
#         imgs = driver.find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
#         if index >= len(imgs):
#             log.error(f"圖片索引 {index} 超出範圍（共 {len(imgs)} 張）")
#             return False

#         target_img = imgs[index]
#         # 點擊圖片或其父層連結
#         try:
#             parent_link = target_img.find_element(By.XPATH, "./ancestor::a[1]")
#             parent_link.click()
#             log.info(f"✅ 已點擊第 {index+1} 張課程圖片（父連結）")
#         except NoSuchElementException:
#             target_img.click()
#             log.info(f"✅ 已點擊第 {index+1} 張課程圖片（直接點圖）")

#         time.sleep(2)

#     except StaleElementReferenceException:
#         log.warning("元素已過期，重新取得圖片")
#         try:
#             imgs = driver.find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
#             imgs[index].click()
#             time.sleep(2)
#         except Exception as e:
#             log.error(f"重試點擊圖片失敗：{e}")
#             return False

#     except Exception as e:
#         log.error(f"點擊課程圖片時發生錯誤：{e}")
#         driver.save_screenshot(f"course_{index+1}_img_failed.png")
#         return False

#     # ── Step 4：點擊「上課去」按鈕 ───────────────────────────────────
#     log.info("── Step 4：點擊「上課去」")
#     try:
#         # onclick="gotoCourse('...')" 或 class 包含 btnAction
#         goto_btn = wait.until(
#             EC.element_to_be_clickable((
#                 By.CSS_SELECTOR,
#                 "button.btnAction[onclick*='gotoCourse'], "
#                 "button.btn-blue.btnAction, "
#                 ".btnAction"
#             ))
#         )
#         course_id = _extract_course_id(goto_btn)
#         goto_btn.click()
#         log.info(f"✅ 已點擊「上課去」（課程ID：{course_id}）")
#         time.sleep(3)

#         # ── 啟動防閒置迴圈（背景執行緒）────────────────────────────────
#         log.info("🔄 啟動防閒置迴圈")
#         idle_thread = threading.Thread(
#             target=run_anti_idle_loop,
#             args=(driver, config.ANTI_IDLE_INTERVAL, stop_flag),
#             daemon=True,
#             name=f"AntiIdle-course{index+1}",
#         )
#         idle_thread.start()

#         # ── 監控：持續檢查是否有錯誤，等執行緒結束才繼續 ────────────────
#         log.info("👀 監控防閒置迴圈中（等待完成或錯誤）...")
#         error_occurred = _watch_idle_thread(driver, idle_thread, stop_flag, index)
#         if error_occurred:
#             return False

#         log.info(f"✅ 第 {index+1} 門課程防閒置迴圈已結束，準備繼續下一門")
#         return True

#     except TimeoutException:
#         log.error("❌ 找不到「上課去」按鈕")
#         driver.save_screenshot(f"course_{index+1}_goto_failed.png")
#         return False


# def _watch_idle_thread(
#     driver: webdriver.Chrome,
#     idle_thread: threading.Thread,
#     stop_flag: list,
#     index: int,
#     check_interval: int = 5,
# ) -> bool:
#     """
#     監控防閒置執行緒，每隔 check_interval 秒檢查一次 WebDriver 狀態。

#     Returns:
#         True  → 偵測到錯誤（呼叫端應視為失敗）
#         False → 正常結束（stop_flag[0] 被設為 True 或執行緒自然退出）
#     """
#     while idle_thread.is_alive():
#         time.sleep(check_interval)

#         # 若外部已設定停止旗標，直接等執行緒收尾後離開
#         if stop_flag[0]:
#             idle_thread.join(timeout=10)
#             return False

#         # 定期 ping 瀏覽器，確認連線正常
#         try:
#             _ = driver.current_url  # 最輕量的 WebDriver 呼叫
#         except WebDriverException as e:
#             log.error(f"⚠️  [監控] 第 {index+1} 門課偵測到 WebDriver 錯誤：{e}")
#             stop_flag[0] = True      # 通知防閒置迴圈停止
#             idle_thread.join(timeout=10)
#             return True
#         except Exception as e:
#             log.error(f"⚠️  [監控] 第 {index+1} 門課發生未預期錯誤：{e}")
#             stop_flag[0] = True
#             idle_thread.join(timeout=10)
#             return True

#     return False  # 執行緒自然結束，無錯誤


# def _extract_course_id(btn) -> str:
#     """從 onclick 屬性取出課程 ID，例如 gotoCourse('10042574') → '10042574'。"""
#     try:
#         onclick = btn.get_attribute("onclick") or ""
#         # gotoCourse('12345')
#         start = onclick.find("'") + 1
#         end = onclick.find("'", start)
#         return onclick[start:end] if start > 0 else "unknown"
#     except Exception:
#         return "unknown"


# # ── 單獨執行測試 ──────────────────────────────────────────────────────
# if __name__ == "__main__":
#     import sys, os
#     sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
#     from open_browser import open_browser
#     from login import login

#     driver = open_browser()
#     driver.get(config.BASE_URL)
#     if login(driver):
#         success = find_and_start_course(driver)
#         if success:
#             input("✅ 已進入課程！按 Enter 關閉...")
#         else:
#             input("❌ 進入課程失敗，按 Enter 關閉...")
#     driver.quit()



"""
3_find_and_start_course.py
功能：登入後依序完成以下流程：
  Step 1. 點擊「個人專區」
  Step 2. 點擊「學習中課程」tab（title 不固定）
  Step 3. 偵測課程圖片數量，依序進入每門課程
  Step 4. 點擊「上課去」按鈕，啟動防閒置（10~15 分鐘隨機間隔）
"""

import time
import random
import re
import logging
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)

import config
from anti_idle import run_anti_idle_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

PERSONAL_AREA_URL = "https://elearn.hrd.gov.tw/mooc/user/learn_dashboard.php"


def _click(wait: WebDriverWait, by, selector: str, desc: str) -> bool:
    try:
        el = wait.until(EC.element_to_be_clickable((by, selector)))
        el.click()
        log.info(f"✅ {desc}")
        time.sleep(1.5)
        return True
    except TimeoutException:
        log.error(f"❌ 逾時找不到：{desc}（selector: {selector}）")
        return False


def find_and_start_course(
    driver: webdriver.Chrome,
    stop_flag: list = None,
) -> bool:
    if stop_flag is None:
        stop_flag = [False]
    wait = WebDriverWait(driver, config.PAGE_LOAD_TIMEOUT)

    log.info("Step 1: Click 已點擊「個人專區」")
    if not _click(wait, By.CSS_SELECTOR,
                  "a[href*='learn_dashboard.php'][title='個人專區']",
                  "已點擊「個人專區」"):
        if not _click(wait, By.CSS_SELECTOR,
                      "a[href*='learn_dashboard.php']",
                      "已點擊「個人專區」 fallback"):
            driver.save_screenshot("step1_personal_failed.png")
            return False

    log.info("Step 2: Click 已點擊學習中課程 tab")
    if not _click(wait, By.CSS_SELECTOR,
                  "a[href*='learn_dashboard.php?tab=1']",
                  "已點擊學習中課程 tab"):
        driver.save_screenshot("step2_tab_failed.png")
        return False

    log.info("── Step 3：偵測課程圖片數量")
    try:
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "img[alt='課程代表圖']")))
        course_imgs = driver.find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
    except TimeoutException:
        log.error("❌ 找不到任何課程圖片，請確認已有報名中的課程")
        driver.save_screenshot("step3_no_course.png")
        return False

    total = len(course_imgs)
    log.info(f"共找到 {total} 門課程")
    if total == 0:
        return False

    for i in range(total):
        log.info(f"{'='*40}\n處理第 {i+1} / {total} 門課程\n{'='*40}")
        course_stop_flag = [False]
        success = _process_single_course(driver, wait, i, total, course_stop_flag)
        if not success:
            log.warning(f"第 {i+1} 門課程處理失敗，繼續下一門")

        if i < total - 1:
            log.info("返回課程列表...")
            driver.get(PERSONAL_AREA_URL + "?tab=1")
            time.sleep(2)
            try:
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "img[alt='課程代表圖']")))
            except TimeoutException:
                log.warning("返回後找不到課程圖片")

    log.info("✅ 所有課程處理完畢")
    return True


def _get_cert_hours(driver: webdriver.Chrome, index: int):
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, "div.course-list-inner")
        if index >= len(cards):
            log.warning(f"課程卡片索引 {index} 超出範圍（共 {len(cards)} 張）")
            return None

        card_html = cards[index].get_attribute("innerHTML") or ""

        match = re.search(
            r'認證時數\s*:\s*</div>\s*<div[^>]*>\s*&nbsp;\s*([\d.]+)\s*小時',
            card_html,
        )
        if match:
            hours = float(match.group(1))
            log.info(f"📋 第 {index+1} 門課程認證時數：{hours} 小時")
            return hours

        hour_els = cards[index].find_elements(
            By.XPATH,
            ".//*[contains(text(),'認證時數')]/following-sibling::div"
        )
        for el in hour_els:
            m = re.search(r'([\d.]+)', el.text.strip())
            if m:
                hours = float(m.group(1))
                log.info(f"📋 第 {index+1} 門課程認證時數（備用）：{hours} 小時")
                return hours

        log.warning(f"⚠️  第 {index+1} 門課程找不到認證時數")
        return None

    except Exception as e:
        log.warning(f"⚠️  解析認證時數時發生錯誤：{e}")
        return None


def _process_single_course(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    index: int,
    total: int,
    stop_flag: list = None,
) -> bool:
    if stop_flag is None:
        stop_flag = [False]

    cert_hours = _get_cert_hours(driver, index)
    max_idle_secs = int(cert_hours * 3600 * 0.53) if cert_hours is not None else None
    if max_idle_secs is not None:
        log.info(f"⏱️  防閒置上限：{max_idle_secs // 60} 分鐘（認證時數 {cert_hours}h × 0.53）")
    else:
        log.warning("⚠️  無法取得認證時數，防閒置將持續直到 stop_flag 被設定")

    try:
        imgs = driver.find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
        if index >= len(imgs):
            log.error(f"圖片索引 {index} 超出範圍（共 {len(imgs)} 張）")
            return False

        target_img = imgs[index]
        try:
            parent_link = target_img.find_element(By.XPATH, "./ancestor::a[1]")
            parent_link.click()
            log.info(f"✅ 已點擊第 {index+1} 張課程圖片（父連結）")
        except NoSuchElementException:
            target_img.click()
            log.info(f"✅ 已點擊第 {index+1} 張課程圖片（直接點圖）")
        time.sleep(2)

    except StaleElementReferenceException:
        log.warning("元素已過期，重新取得圖片")
        try:
            imgs = driver.find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
            imgs[index].click()
            time.sleep(2)
        except Exception as e:
            log.error(f"重試點擊圖片失敗：{e}")
            return False
    except Exception as e:
        log.error(f"點擊課程圖片時發生錯誤：{e}")
        driver.save_screenshot(f"course_{index+1}_img_failed.png")
        return False

    log.info("── Step 4：點擊「上課去」")
    try:
        goto_btn = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "button.btnAction[onclick*='gotoCourse'], "
            "button.btn-blue.btnAction, "
            ".btnAction"
        )))
        course_id = _extract_course_id(goto_btn)
        goto_btn.click()
        log.info(f"✅ 已點擊「上課去」（課程ID：{course_id}）")
        time.sleep(3)

        idle_interval = random.randint(10 * 60, 12 * 60)
        log.info(f"🔄 啟動防閒置迴圈（間隔：{idle_interval // 60} 分鐘）")
        idle_thread = threading.Thread(
            target=run_anti_idle_loop,
            args=(driver, idle_interval, stop_flag),
            daemon=True,
            name=f"AntiIdle-course{index+1}",
        )
        idle_thread.start()

        log.info("👀 監控防閒置迴圈中（等待完成、超時或錯誤）...")
        error_occurred = _watch_idle_thread(
            driver, idle_thread, stop_flag, index, max_idle_secs=max_idle_secs
        )
        if error_occurred:
            return False

        log.info(f"✅ 第 {index+1} 門課程防閒置迴圈已結束，準備繼續下一門")
        return True

    except TimeoutException:
        log.error("❌ 找不到「上課去」按鈕")
        driver.save_screenshot(f"course_{index+1}_goto_failed.png")
        return False


def _watch_idle_thread(
    driver: webdriver.Chrome,
    idle_thread: threading.Thread,
    stop_flag: list,
    index: int,
    check_interval: int = 5,
    max_idle_secs: int = None,
) -> bool:
    start_time = time.time()

    while idle_thread.is_alive():
        time.sleep(check_interval)
        elapsed = time.time() - start_time

        if max_idle_secs is not None and elapsed >= max_idle_secs:
            log.info(f"⏰ 第 {index+1} 門課已執行 {int(elapsed // 60)} 分鐘（上限 {max_idle_secs // 60} 分鐘），停止防閒置")
            stop_flag[0] = True
            idle_thread.join(timeout=10)
            return False

        if stop_flag[0]:
            idle_thread.join(timeout=10)
            return False

        try:
            _ = driver.current_url
        except WebDriverException as e:
            log.error(f"⚠️  [監控] 第 {index+1} 門課偵測到 WebDriver 錯誤：{e}")
            stop_flag[0] = True
            idle_thread.join(timeout=10)
            return True
        except Exception as e:
            log.error(f"⚠️  [監控] 第 {index+1} 門課發生未預期錯誤：{e}")
            stop_flag[0] = True
            idle_thread.join(timeout=10)
            return True

    return False


def _extract_course_id(btn) -> str:
    try:
        onclick = btn.get_attribute("onclick") or ""
        start = onclick.find("'") + 1
        end = onclick.find("'", start)
        return onclick[start:end] if start > 0 else "unknown"
    except Exception:
        return "unknown"


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from open_browser import open_browser
    from login import login

    driver = open_browser()
    driver.get(config.BASE_URL)
    if login(driver):
        success = find_and_start_course(driver)
        if success:
            input("✅ 已進入課程！按 Enter 關閉...")
        else:
            input("❌ 進入課程失敗，按 Enter 關閉...")
    driver.quit()