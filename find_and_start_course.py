# """
# 3_find_and_start_course.py
# 功能：登入後依序完成以下流程：
#   Step 1. 點擊「個人專區」
#   Step 2. 點擊「學習中課程」tab（title 不固定）
#   Step 3. 偵測課程圖片數量，依序進入每門課程
#   Step 3.5. 判斷課程是否已完成（閱讀時數 + 問卷狀態），符合則跳過
#   Step 4. 點擊「上課去」按鈕，啟動防閒置（10~12 分鐘隨機間隔）
# """

# import time
# import random
# import re
# import logging
# import threading
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import (
#     TimeoutException,
#     NoSuchElementException,
#     StaleElementReferenceException,
#     WebDriverException,
# )

# import config
# from anti_idle import run_anti_idle_loop
# from fill_questionnaire import fill_questionnaire

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
# )
# log = logging.getLogger(__name__)

# PERSONAL_AREA_URL = "https://elearn.hrd.gov.tw/mooc/user/learn_dashboard.php"


# def _click(wait: WebDriverWait, by, selector: str, desc: str) -> bool:
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
#     if stop_flag is None:
#         stop_flag = [False]
#     wait = WebDriverWait(driver, config.PAGE_LOAD_TIMEOUT)

#     log.info("── Step 1：點擊「個人專區」")
#     if not _click(wait, By.CSS_SELECTOR,
#                   "a[href*='learn_dashboard.php'][title='個人專區']",
#                   "已點擊「個人專區」"):
#         if not _click(wait, By.CSS_SELECTOR,
#                       "a[href*='learn_dashboard.php']",
#                       "已點擊「個人專區」 fallback"):
#             driver.save_screenshot("step1_personal_failed.png")
#             return False

#     log.info("── Step 2：點擊學習中課程 tab")
#     if not _click(wait, By.CSS_SELECTOR,
#                   "a[href*='learn_dashboard.php?tab=1']",
#                   "已點擊學習中課程 tab"):
#         driver.save_screenshot("step2_tab_failed.png")
#         return False

#     # ── Step 2.5：偵測「了解，我清楚了」視窗（可選，出現才點） ────────
#     _dismiss_notice_popup(driver)

#     log.info("── Step 3：偵測課程圖片數量")
#     try:
#         wait.until(EC.presence_of_element_located(
#             (By.CSS_SELECTOR, "img[alt='課程代表圖']")))
#         course_imgs = driver.find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
#     except TimeoutException:
#         log.error("❌ 找不到任何課程圖片，請確認已有報名中的課程")
#         driver.save_screenshot("step3_no_course.png")
#         return False

#     total = len(course_imgs)
#     log.info(f"共找到 {total} 門課程")
#     if total == 0:
#         return False

#     for i in range(total):
#         log.info(f"{'='*40}\n處理第 {i+1} / {total} 門課程\n{'='*40}")
#         course_stop_flag = [False]
#         success = _process_single_course(driver, wait, i, total, course_stop_flag)
#         if not success:
#             log.warning(f"第 {i+1} 門課程處理失敗，繼續下一門")

#         if i < total - 1:
#             log.info("返回課程列表...")
#             driver.get(PERSONAL_AREA_URL + "?tab=1")
#             time.sleep(2)
#             try:
#                 wait.until(EC.presence_of_element_located(
#                     (By.CSS_SELECTOR, "img[alt='課程代表圖']")))
#             except TimeoutException:
#                 log.warning("返回後找不到課程圖片")

#     log.info("✅ 所有課程處理完畢")
#     return True


# # ══════════════════════════════════════════════════════════════════════
# # 輔助函式
# # ══════════════════════════════════════════════════════════════════════

# def _dismiss_notice_popup(driver: webdriver.Chrome, timeout: int = 5):
#     """偵測「了解，我清楚了」視窗，出現才點擊，沒有則靜默略過。"""
#     selectors = [
#         (By.XPATH, "//button[contains(text(),'了解，我清楚了')]"),
#         (By.XPATH, "//button[contains(text(),'我清楚了')]"),
#         (By.XPATH, "//a[contains(text(),'了解，我清楚了')]"),
#         (By.XPATH, "//a[contains(text(),'我清楚了')]"),
#     ]
#     short_wait = WebDriverWait(driver, timeout)
#     for by, selector in selectors:
#         try:
#             btn = short_wait.until(EC.element_to_be_clickable((by, selector)))
#             btn.click()
#             log.info("✅ 已關閉通知視窗（了解，我清楚了）")
#             time.sleep(1)
#             return
#         except TimeoutException:
#             continue
#         except Exception as e:
#             log.warning(f"關閉通知視窗時發生問題：{e}")
#             continue
#     log.info("ℹ️  未偵測到通知視窗，繼續執行")


# def _parse_read_seconds(time_str: str) -> int:
#     """
#     將「HH:MM:SS」格式字串轉換為秒數。
#     例如 "00:02:20" → 140，"01:30:00" → 5400
#     """
#     try:
#         parts = time_str.strip().split(":")
#         if len(parts) == 3:
#             h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
#             return h * 3600 + m * 60 + s
#         elif len(parts) == 2:
#             m, s = int(parts[0]), int(parts[1])
#             return m * 60 + s
#     except Exception:
#         pass
#     return 0


# def _is_already_completed(
#     driver: webdriver.Chrome,
#     cert_hours: float,
#     read_ratio: float = 0.53,
# ) -> bool:
#     """
#     判斷課程是否已達完成條件（兩者同時成立才跳過）：
#       條件 1：閱讀時數 > 認證時數 × read_ratio（預設 0.53）
#       條件 2：問卷狀態為「已填」

#     資料來源：div.majorstatus 內的子 div 文字。
#     任一條件未達成或解析失敗，回傳 False（繼續上課）。
#     """
#     if cert_hours is None:
#         log.warning("⚠️  認證時數未知，無法判斷完成狀態，繼續上課")
#         return False

#     threshold_secs = cert_hours * 3600 * 0.5

#     try:
#         # ── 取得 div.majorstatus 內所有子 div ────────────────────────
#         status_divs = driver.find_elements(
#             By.CSS_SELECTOR, "div.majorstatus > div"
#         )
#         if not status_divs:
#             log.warning("⚠️  找不到 div.majorstatus，無法判斷完成狀態")
#             return False

#         read_secs = None
#         survey_status = None

#         for div in status_divs:
#             text = div.text.strip()
#             log.info(f"[majorstatus] {text}")

#             # 閱讀時數：HH:MM:SS
#             if text.startswith("閱讀時數"):
#                 m = re.search(r"(\d{1,3}:\d{2}:\d{2})", text)
#                 if m:
#                     read_secs = _parse_read_seconds(m.group(1))
#                     log.info(f"📖 閱讀時數：{m.group(1)}（{read_secs}s）")

#             # 問卷：已填 / 未填
#             elif text.startswith("問卷"):
#                 # text 可能是「問卷：已填」或「問卷：未填」
#                 if "已填" in text:
#                     survey_status = "已填"
#                 elif "未填" in text:
#                     survey_status = "未填"
#                 log.info(f"📋 問卷狀態：{survey_status}")

#         # ── 條件 1：閱讀時數 ─────────────────────────────────────────
#         if read_secs is None:
#             log.info("ℹ️  找不到閱讀時數，視為未達門檻")
#             return False

#         log.info(
#             f"⏱️  門檻：{int(threshold_secs)}s"
#         )
#         if read_secs < threshold_secs:
#             log.info("ℹ️  閱讀時數未達門檻，繼續上課")
#             return False

#         # ── 條件 2：問卷狀態 ─────────────────────────────────────────
#         if survey_status != "已填":
#             log.info("ℹ️  問卷尚未填寫，繼續上課")
#             return False

#         log.info("✅ 閱讀時數足夠且問卷已填，此課程可跳過")
#         return True

#     except Exception as e:
#         log.warning(f"⚠️  判斷完成狀態時發生錯誤：{e}")
#         return False


# def _get_cert_hours(driver: webdriver.Chrome, index: int):
#     """
#     從第 index 張課程卡片中解析「認證時數」。
#     Returns: float（小時）或 None（解析失敗）
#     """
#     try:
#         cards = driver.find_elements(By.CSS_SELECTOR, "div.course-list-inner")
#         if index >= len(cards):
#             log.warning(f"課程卡片索引 {index} 超出範圍（共 {len(cards)} 張）")
#             return None

#         card_html = cards[index].get_attribute("innerHTML") or ""

#         match = re.search(
#             r'認證時數\s*:\s*</div>\s*<div[^>]*>\s*&nbsp;\s*([\d.]+)\s*小時',
#             card_html,
#         )
#         if match:
#             hours = float(match.group(1))
#             log.info(f"📋 第 {index+1} 門課程認證時數：{hours} 小時")
#             return hours

#         hour_els = cards[index].find_elements(
#             By.XPATH,
#             ".//*[contains(text(),'認證時數')]/following-sibling::div"
#         )
#         for el in hour_els:
#             m = re.search(r'([\d.]+)', el.text.strip())
#             if m:
#                 hours = float(m.group(1))
#                 log.info(f"📋 第 {index+1} 門課程認證時數（備用）：{hours} 小時")
#                 return hours

#         log.warning(f"⚠️  第 {index+1} 門課程找不到認證時數")
#         return None

#     except Exception as e:
#         log.warning(f"⚠️  解析認證時數時發生錯誤：{e}")
#         return None


# def _process_single_course(
#     driver: webdriver.Chrome,
#     wait: WebDriverWait,
#     index: int,
#     total: int,
#     stop_flag: list = None,
# ) -> bool:
#     """
#     處理單一課程：
#       解析認證時數 → 點擊課程圖片 → Step 3.5 完成判斷 →
#       點「上課去」→ 啟動防閒置 → 監控 → 填寫問卷
#     """
#     if stop_flag is None:
#         stop_flag = [False]

#     # ── 解析認證時數（供後續防閒置上限 & 完成判斷使用）────────────────
#     cert_hours = _get_cert_hours(driver, index)
#     max_idle_secs = int(cert_hours * 3600 * 0.525) if cert_hours is not None else None
#     if max_idle_secs is not None:
#         log.info(f"⏱️  防閒置上限：{max_idle_secs // 60} 分鐘（認證時數 {cert_hours}h × 0.525）")
#     else:
#         log.warning("⚠️  無法取得認證時數，防閒置將持續直到 stop_flag 被設定")

#     # ── Step 3-a：點擊課程圖片 ────────────────────────────────────────
#     try:
#         imgs = driver.find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
#         if index >= len(imgs):
#             log.error(f"圖片索引 {index} 超出範圍（共 {len(imgs)} 張）")
#             return False

#         target_img = imgs[index]
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

#     # ── Step 3.5：判斷課程是否已完成（閱讀時數 + 問卷狀態）────────────
#     log.info("── Step 3.5：檢查課程完成狀態")
#     if _is_already_completed(driver, cert_hours):
#         log.info(f"⏭️  第 {index+1} 門課程已達完成條件，跳過上課直接進入下一門")
#         return True

#     # ── Step 4：點擊「上課去」按鈕 ───────────────────────────────────
#     log.info("── Step 4：點擊「上課去」")
#     try:
#         goto_btn = wait.until(EC.element_to_be_clickable((
#             By.CSS_SELECTOR,
#             "button.btnAction[onclick*='gotoCourse'], "
#             "button.btn-blue.btnAction, "
#             ".btnAction"
#         )))
#         course_id = _extract_course_id(goto_btn)
#         goto_btn.click()
#         log.info(f"✅ 已點擊「上課去」（課程ID：{course_id}）")
#         time.sleep(3)

#         idle_interval = random.randint(10 * 60, 12 * 60)
#         log.info(f"🔄 啟動防閒置迴圈（間隔：{idle_interval // 60} 分鐘）")
#         idle_thread = threading.Thread(
#             target=run_anti_idle_loop,
#             args=(driver, idle_interval, stop_flag),
#             daemon=True,
#             name=f"AntiIdle-course{index+1}",
#         )
#         idle_thread.start()

#         log.info("👀 監控防閒置迴圈中（等待完成、超時或錯誤）...")
#         error_occurred = _watch_idle_thread(
#             driver, idle_thread, stop_flag, index, max_idle_secs=max_idle_secs
#         )
#         if error_occurred:
#             return False

#         log.info(f"✅ 第 {index+1} 門課程防閒置迴圈已結束，準備繼續下一門")

#         # ── 填寫問卷（防閒置結束後、跳下一門課前）─────────────────────
#         log.info("📝 嘗試填寫問卷/評價...")
#         try:
#             fill_questionnaire(driver)
#         except Exception as e:
#             log.warning(f"⚠️  填寫問卷時發生錯誤（不影響後續流程）：{e}")

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
#     max_idle_secs: int = None,
# ) -> bool:
#     """
#     監控防閒置執行緒，每隔 check_interval 秒 ping 一次瀏覽器。
#     超過 max_idle_secs 或偵測到錯誤時停止。

#     Returns:
#         True  → 偵測到錯誤（呼叫端應視為失敗）
#         False → 正常結束（超時 / stop_flag / 執行緒自然退出）
#     """
#     start_time = time.time()

#     while idle_thread.is_alive():
#         time.sleep(check_interval)
#         elapsed = time.time() - start_time

#         if max_idle_secs is not None and elapsed >= max_idle_secs:
#             log.info(
#                 f"⏰ 第 {index+1} 門課已執行 {int(elapsed // 60)} 分鐘"
#                 f"（上限 {max_idle_secs // 60} 分鐘），停止防閒置"
#             )
#             stop_flag[0] = True
#             idle_thread.join(timeout=10)
#             return False

#         if stop_flag[0]:
#             idle_thread.join(timeout=10)
#             return False

#         try:
#             _ = driver.current_url
#         except WebDriverException as e:
#             log.error(f"⚠️  [監控] 第 {index+1} 門課偵測到 WebDriver 錯誤：{e}")
#             stop_flag[0] = True
#             idle_thread.join(timeout=10)
#             return True
#         except Exception as e:
#             log.error(f"⚠️  [監控] 第 {index+1} 門課發生未預期錯誤：{e}")
#             stop_flag[0] = True
#             idle_thread.join(timeout=10)
#             return True

#     return False


# def _extract_course_id(btn) -> str:
#     """從 onclick 屬性取出課程 ID。"""
#     try:
#         onclick = btn.get_attribute("onclick") or ""
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
  Step 3.5. 判斷課程是否已完成（閱讀時數 + 問卷狀態），符合則跳過
  Step 4. 點擊「上課去」按鈕，啟動防閒置（10~12 分鐘隨機間隔）
  Step 5. 所有課程完成後，偵測是否有下一頁，有則繼續
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
from fill_questionnaire import fill_questionnaire

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

    log.info("── Step 1：點擊「個人專區」")
    if not _click(wait, By.CSS_SELECTOR,
                  "a[href*='learn_dashboard.php'][title='個人專區']",
                  "已點擊「個人專區」"):
        if not _click(wait, By.CSS_SELECTOR,
                      "a[href*='learn_dashboard.php']",
                      "已點擊「個人專區」 fallback"):
            driver.save_screenshot("step1_personal_failed.png")
            return False

    log.info("── Step 2：點擊學習中課程 tab")
    if not _click(wait, By.CSS_SELECTOR,
                  "a[href*='learn_dashboard.php?tab=1']",
                  "已點擊學習中課程 tab"):
        driver.save_screenshot("step2_tab_failed.png")
        return False

    # ── Step 2.5：偵測「了解，我清楚了」視窗（可選，出現才點） ────────
    _dismiss_notice_popup(driver)

    # ── 逐頁處理，每頁完成後偵測是否有下一頁 ─────────────────────────
    page_num = 1
    while True:
        log.info(f"── Step 3：偵測第 {page_num} 頁課程圖片數量")
        try:
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "img[alt='課程代表圖']")))
            course_imgs = driver.find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
        except TimeoutException:
            log.error("❌ 找不到任何課程圖片，請確認已有報名中的課程")
            driver.save_screenshot("step3_no_course.png")
            return False

        total = len(course_imgs)
        log.info(f"第 {page_num} 頁共找到 {total} 門課程")
        if total == 0:
            return False

        for i in range(total):
            log.info(f"{'='*40}\n處理第 {i+1} / {total} 門課程（第 {page_num} 頁）\n{'='*40}")
            course_stop_flag = [False]
            success = _process_single_course(driver, wait, i, total, course_stop_flag)
            if not success:
                log.warning(f"第 {i+1} 門課程處理失敗，繼續下一門")

            if i < total - 1:
                log.info("返回課程列表...")
                driver.get(PERSONAL_AREA_URL + "?tab=1")
                time.sleep(2)
                # 若不在第一頁，需翻回當前頁
                if page_num > 1:
                    _navigate_to_page(driver, wait, page_num)
                try:
                    wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "img[alt='課程代表圖']")))
                except TimeoutException:
                    log.warning("返回後找不到課程圖片")

        # ── 本頁全部完成，偵測是否有下一頁 ──────────────────────────
        log.info(f"✅ 第 {page_num} 頁所有課程處理完畢，檢查是否有下一頁...")

        # 先返回課程列表，再偵測下一頁
        log.info("返回課程列表...")
        driver.get(PERSONAL_AREA_URL + "?tab=1")
        time.sleep(2)
        if page_num > 1:
            _navigate_to_page(driver, wait, page_num)
        try:
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "img[alt='課程代表圖']")))
        except TimeoutException:
            log.warning("返回後找不到課程圖片，結束")
            break

        if _go_to_next_page(driver, wait):
            page_num += 1
            time.sleep(2)
            try:
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "img[alt='課程代表圖']")))
            except TimeoutException:
                log.warning("翻頁後找不到課程圖片，結束")
                break
        else:
            log.info("✅ 已無下一頁，所有課程處理完畢")
            break

    return True


# ══════════════════════════════════════════════════════════════════════
# 輔助函式
# ══════════════════════════════════════════════════════════════════════

def _go_to_next_page(driver: webdriver.Chrome, wait: WebDriverWait) -> bool:
    """
    偵測並點擊下一頁按鈕 <i class="paginate-next">。
    有下一頁且點擊成功回傳 True，否則回傳 False。
    """
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "i.paginate-next")
        parent = next_btn.find_element(By.XPATH, "..")  # 父層 <a>

        parent_class = parent.get_attribute("class") or ""
        parent_title = parent.get_attribute("title") or ""

        # # 此分頁元件用 class="undefined" 表示該按鈕無作用（停用）
        # if "undefined" in parent_class.lower():
        #     log.info("ℹ️  下一頁按鈕為 undefined（已是最後一頁）")
        #     return False

        # 額外防呆：沒有 title 或 href 也視為無效
        parent_href = parent.get_attribute("href") or ""
        if not parent_href and not parent_title:
            log.info("ℹ️  下一頁按鈕無 href 及 title，視為最後一頁")
            return False

        next_btn.click()
        log.info("➡️  已點擊下一頁")
        time.sleep(2)
        return True

    except NoSuchElementException:
        log.info("ℹ️  找不到下一頁按鈕，已是最後一頁")
        return False
    except Exception as e:
        log.warning(f"⚠️  點擊下一頁時發生錯誤：{e}")
        return False


def _navigate_to_page(driver: webdriver.Chrome, wait: WebDriverWait, target_page: int):
    """返回課程列表後，翻頁至 target_page（從第 1 頁點 target_page-1 次下一頁）。"""
    for _ in range(target_page - 1):
        if not _go_to_next_page(driver, wait):
            log.warning("⚠️  翻頁至目標頁時失敗，可能頁數不足")
            break
        time.sleep(1)


def _dismiss_notice_popup(driver: webdriver.Chrome, timeout: int = 5):
    """偵測「了解，我清楚了」視窗，出現才點擊，沒有則靜默略過。"""
    selectors = [
        (By.XPATH, "//button[contains(text(),'了解，我清楚了')]"),
        (By.XPATH, "//button[contains(text(),'我清楚了')]"),
        (By.XPATH, "//a[contains(text(),'了解，我清楚了')]"),
        (By.XPATH, "//a[contains(text(),'我清楚了')]"),
    ]
    short_wait = WebDriverWait(driver, timeout)
    for by, selector in selectors:
        try:
            btn = short_wait.until(EC.element_to_be_clickable((by, selector)))
            btn.click()
            log.info("✅ 已關閉通知視窗（了解，我清楚了）")
            time.sleep(1)
            return
        except TimeoutException:
            continue
        except Exception as e:
            log.warning(f"關閉通知視窗時發生問題：{e}")
            continue
    log.info("ℹ️  未偵測到通知視窗，繼續執行")


def _parse_read_seconds(time_str: str) -> int:
    """
    將「HH:MM:SS」格式字串轉換為秒數。
    例如 "00:02:20" → 140，"01:30:00" → 5400
    """
    try:
        parts = time_str.strip().split(":")
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = int(parts[0]), int(parts[1])
            return m * 60 + s
    except Exception:
        pass
    return 0


def _is_already_completed(
    driver: webdriver.Chrome,
    cert_hours: float,
    read_ratio: float = 0.5,
) -> tuple:
    """
    判斷課程狀態，回傳 (status, read_secs)。

    status 可能值：
      "completed"   → 閱讀時數足夠且問卷已填，可直接跳過
      "need_survey" → 閱讀時數足夠但問卷未填，需填寫問卷
      "in_progress" → 閱讀時數未達門檻，繼續上課
      "unknown"     → 無法判斷（解析失敗），視同 in_progress

    read_secs：已閱讀秒數，供計算防閒置上限用，無法取得時為 0。
    """
    if cert_hours is None:
        log.warning("⚠️  認證時數未知，無法判斷完成狀態，繼續上課")
        return "unknown", 0

    threshold_secs = cert_hours * 3600 * read_ratio

    try:
        status_divs = driver.find_elements(
            By.CSS_SELECTOR, "div.majorstatus > div"
        )
        if not status_divs:
            log.warning("⚠️  找不到 div.majorstatus，無法判斷完成狀態")
            return "unknown", 0

        read_secs = None
        survey_status = None

        for div in status_divs:
            text = div.text.strip()
            log.info(f"[majorstatus] {text}")

            if text.startswith("閱讀時數"):
                m = re.search(r"(\d{1,3}:\d{2}:\d{2})", text)
                if m:
                    read_secs = _parse_read_seconds(m.group(1))
                    log.info(f"📖 閱讀時數：{m.group(1)}（{read_secs}s）")

            elif text.startswith("問卷"):
                if "已填" in text:
                    survey_status = "已填"
                elif "未填" in text:
                    survey_status = "未填"
                log.info(f"📋 問卷狀態：{survey_status}")

        if read_secs is None:
            log.info("ℹ️  找不到閱讀時數，視為未達門檻")
            return "in_progress", 0

        log.info(f"⏱️  門檻：{int(threshold_secs)}s（認證 {cert_hours}h ）")

        if read_secs < threshold_secs:
            log.info("ℹ️  閱讀時數未達門檻，繼續上課")
            return "in_progress", read_secs

        # 閱讀時數已達門檻，看問卷
        if survey_status != "已填":
            log.info("ℹ️  閱讀時數足夠，但問卷尚未填寫")
            return "need_survey", read_secs

        log.info("✅ 閱讀時數足夠且問卷已填，此課程可跳過")
        return "completed", read_secs

    except Exception as e:
        log.warning(f"⚠️  判斷完成狀態時發生錯誤：{e}")
        return "unknown", 0


def _get_cert_hours(driver: webdriver.Chrome, index: int):
    """
    從第 index 張課程卡片中解析「認證時數」。
    Returns: float（小時）或 None（解析失敗）
    """
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
    """
    處理單一課程：
      解析認證時數 → 點擊課程圖片 → Step 3.5 完成判斷 →
      點「上課去」→ 啟動防閒置 → 監控 → 填寫問卷
    """
    if stop_flag is None:
        stop_flag = [False]

    # ── 解析認證時數（進課程頁後才取得閱讀時數，max_idle_secs 在 3.5 後計算）──
    cert_hours = _get_cert_hours(driver, index)

    # ── Step 3-a：點擊課程圖片 ────────────────────────────────────────
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

    # ── Step 3.5：判斷課程狀態，同時取得 read_secs ───────────────────
    log.info("── Step 3.5：檢查課程完成狀態")
    status, read_secs = _is_already_completed(driver, cert_hours)

    # ── 計算防閒置上限：cert_hours × 3600 × 0.53 − read_secs ─────────
    if cert_hours is not None:
        max_idle_secs = max(0, int(cert_hours * 3600 * 0.53 - read_secs))
        log.info(
            f"⏱️  防閒置上限：{max_idle_secs // 60} 分 {max_idle_secs % 60} 秒"
            f"（{cert_hours}h × 3600 × 0.53 = {int(cert_hours * 3600 * 0.53)}s"
            f"  −  已讀 {read_secs}s）"
        )
    else:
        max_idle_secs = None
        log.warning("⚠️  無法取得認證時數，防閒置將持續直到 stop_flag 被設定")

    # ── 根據狀態決定後續動作 ─────────────────────────────────────────
    if status == "completed":
        log.info(f"⏭️  第 {index+1} 門課程已達完成條件，跳過上課直接進入下一門")
        return True

    if status == "need_survey":
        log.info(f"📝 第 {index+1} 門課程閱讀時數足夠，直接前往填寫問卷")
        log.info("── Step 4：點擊「上課去」")
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


        try:
            fill_questionnaire(driver)
        except Exception as e:
            log.warning(f"⚠️  填寫問卷時發生錯誤：{e}")
        return True

    # status == "in_progress" 或 "unknown" → 點「上課去」繼續上課

    # ── Step 4：點擊「上課去」按鈕 ───────────────────────────────────
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

        # ── 填寫問卷（防閒置結束後、跳下一門課前）─────────────────────
        log.info("📝 嘗試填寫問卷/評價...")
        try:
            fill_questionnaire(driver)
        except Exception as e:
            log.warning(f"⚠️  填寫問卷時發生錯誤（不影響後續流程）：{e}")

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
    """
    監控防閒置執行緒，每隔 check_interval 秒 ping 一次瀏覽器。
    超過 max_idle_secs 或偵測到錯誤時停止。

    Returns:
        True  → 偵測到錯誤（呼叫端應視為失敗）
        False → 正常結束（超時 / stop_flag / 執行緒自然退出）
    """
    start_time = time.time()

    while idle_thread.is_alive():
        time.sleep(check_interval)
        elapsed = time.time() - start_time

        if max_idle_secs is not None and elapsed >= max_idle_secs:
            log.info(
                f"⏰ 第 {index+1} 門課已執行 {int(elapsed // 60)} 分鐘"
                f"（上限 {max_idle_secs // 60} 分鐘），停止防閒置"
            )
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
    """從 onclick 屬性取出課程 ID。"""
    try:
        onclick = btn.get_attribute("onclick") or ""
        start = onclick.find("'") + 1
        end = onclick.find("'", start)
        return onclick[start:end] if start > 0 else "unknown"
    except Exception:
        return "unknown"


# ── 單獨執行測試 ──────────────────────────────────────────────────────
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