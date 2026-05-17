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
# from do_exam import do_exam  # 確保你有建立此檔案

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
# )
# log = logging.getLogger(__name__)

# PERSONAL_AREA_URL = "https://elearn.hrd.gov.tw/mooc/user/learn_dashboard.php"

# class SessionExpiredError(Exception):
#     """網站偵測到閒置並顯示 alert 強制登出時拋出。"""
#     pass

# def _relogin(driver: webdriver.Chrome) -> webdriver.Chrome:
#     from open_browser import open_browser
#     from login import login
#     log.warning("🔄 帳號已被登出，準備重新開啟瀏覽器並登入...")
#     try:
#         driver.quit()
#     except Exception:
#         pass
#     new_driver = open_browser()
#     new_driver.get(config.BASE_URL)
#     if not login(new_driver):
#         raise RuntimeError("❌ 重新登入失敗，程式無法繼續")
#     log.info("✅ 重新登入成功，繼續學習流程")
#     return new_driver

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

# def find_and_start_course(driver: webdriver.Chrome, stop_flag: list = None, _driver_box: list = None) -> bool:
#     if stop_flag is None: stop_flag = [False]
#     if _driver_box is None: _driver_box = [driver]
#     else: _driver_box[0] = driver

#     def _d() -> webdriver.Chrome: return _driver_box[0]
#     def _w() -> WebDriverWait: return WebDriverWait(_d(), config.PAGE_LOAD_TIMEOUT)

#     MAX_RELOGIN = 5
#     relogin_count = 0

#     while True:
#         try:
#             return _find_and_start_course_inner(_d, _w, stop_flag)
#         except SessionExpiredError:
#             relogin_count += 1
#             if relogin_count > MAX_RELOGIN:
#                 log.error(f"❌ 已連續重登 {MAX_RELOGIN} 次仍失敗，放棄")
#                 return False
#             try:
#                 new_driver = _relogin(_d())
#                 _driver_box[0] = new_driver
#             except RuntimeError as e:
#                 log.error(str(e))
#                 return False

# def _find_and_start_course_inner(_d, _w, stop_flag: list) -> bool:
#     """主要執行邏輯：Phase 1 (學習) -> 開啟輔助工具 -> Phase 2 (測驗) -> 換頁/結束"""

#     while True:
#         log.info("── Step 1：回到「個人專區」")
#         _d().get(PERSONAL_AREA_URL + "?tab=1")
#         time.sleep(2)
#         _dismiss_notice_popup(_d())

#         # 偵測目前頁面課程數量
#         try:
#             _w().until(EC.presence_of_element_located((By.CSS_SELECTOR, "img[alt='課程代表圖']")))
#             course_imgs = _d().find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
#             total_on_page = len(course_imgs)
#         except TimeoutException:
#             log.info("🏁 找不到課程圖片，可能所有課程已完成或頁面為空。")
#             return True

#         if total_on_page == 0:
#             log.info("✅ 目前頁面已無課程")
#             return True

#         # ══════════════════════════════════════════════════════════════
#         # Phase 1：學習與問卷 (1 點到 N)
#         # ══════════════════════════════════════════════════════════════
#         log.info(f"🚀 開始 Phase 1：處理本頁 {total_on_page} 門課程的學習與問卷")
#         for i in range(total_on_page):
#             log.info(f"{'='*30} Phase 1: 第 {i+1} / {total_on_page} 門 {'='*30}")
#             _process_single_course(_d(), _w(), i, stop_flag, phase="study")
#             _d().get(PERSONAL_AREA_URL + "?tab=1")
#             time.sleep(1.5)

#         # ══════════════════════════════════════════════════════════════
#         # Phase 2：測驗迴圈 (執行 N 次，每次都點擊「第一門」)
#         # ══════════════════════════════════════════════════════════════
#         log.info(f"🚀 開始 Phase 2：處理本頁課程測驗 (重複執行 {total_on_page} 次第一門)")
#         for i in range(total_on_page):
#             log.info(f"{'='*30} Phase 2: 第 {i+1} 次測驗流程 {'='*30}")
#             # 注意：這裡固定 index=0，因為完成的課會消失
#             _process_single_course(_d(), _w(), 0, stop_flag, phase="exam")
#             _d().get(PERSONAL_AREA_URL + "?tab=1")
#             time.sleep(1.5)

#         # 檢查是否有下一頁
#         if not _go_to_next_page(_d(), _w()):
#             log.info("✅ 本頁 Phase 1 & 2 結束且無下一頁")
#             break
            
#     return True

# def _process_single_course(driver, wait, index, stop_flag, phase="study") -> bool:
#     """處理單一課程：依據 phase 決定要上課還是測驗"""
#     try:
#         # 1. 解析列表中該課程的認證時數
#         cert_hours = _get_cert_hours(driver, index)
        
#         # 2. 點擊圖片進入課程
#         imgs = driver.find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
#         if index >= len(imgs): return False
#         imgs[index].click()
#         time.sleep(2)

#         # 3. 判斷狀態
#         status, read_secs = _is_already_completed(driver, cert_hours)
        
#         # --- Phase 1: 學習與問卷 ---
#         if phase == "study":
#             if status in ["completed", "need_exam"]:
#                 log.info(f"⏭️ 課程時數已達標 ({status})，跳過學習流程")
#                 return True
            
#             # 啟動上課流程
#             if _start_learning(driver, wait, stop_flag, cert_hours, read_secs):
#                 # 上完課嘗試填問卷
#                 fill_questionnaire(driver)
#                 return True

#         # --- Phase 2: 測驗 ---
#         elif phase == "exam":
#             if status == "completed":
#                 log.info("✅ 此課程測驗已通過且問卷已填，跳過")
#                 return True
            
#             log.info(f"📝 進入測驗流程 (目前狀態: {status})")
#             if _click(wait, By.CSS_SELECTOR, ".btnAction", "點擊上課去"):
#                 time.sleep(3)
#                 do_exam(driver)
#                 return True
                
#     except Exception as e:
#         log.error(f"❌ 處理課程時發生錯誤: {e}")
#     return False

# def _start_learning(driver, wait, stop_flag, cert_hours, read_secs) -> bool:
#     """點擊上課去並執行防閒置"""
#     try:
#         goto_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btnAction")))
#         goto_btn.click()
#         time.sleep(3)
        
#         # 計算需要防閒置的時間
#         if cert_hours:
#             max_idle_secs = max(0, int(cert_hours * 3600 * 0.53 - read_secs))
#         else:
#             max_idle_secs = 1800 # 預設 30 分鐘

#         log.info(f"🔄 啟動防閒置，預計執行 {max_idle_secs} 秒")
#         idle_interval = random.randint(600, 720) # 10-12 分鐘隨機
        
#         stop_flag[0] = False
#         idle_thread = threading.Thread(
#             target=run_anti_idle_loop,
#             args=(driver, idle_interval, stop_flag),
#             daemon=True
#         )
#         idle_thread.start()
        
#         # 監控
#         _watch_idle_thread(driver, idle_thread, stop_flag, 0, max_idle_secs=max_idle_secs)
#         return True
#     except Exception as e:
#         log.error(f"啟動學習失敗: {e}")
#         return False

# def _is_already_completed(driver, cert_hours, read_ratio: float = 0.5) -> tuple:
#     """
#     回傳 (status, read_secs)
#     status: "completed", "need_survey", "need_exam", "in_progress"
#     """
#     if cert_hours is None: return "unknown", 0
#     threshold_secs = cert_hours * 3600 * read_ratio

#     try:
#         status_div = driver.find_element(By.CSS_SELECTOR, "div.majorstatus")
#         text = status_div.text.replace(" ", "")
        
#         read_secs = 0
#         survey_done = "已填" in text
#         exam_score = 0
        
#         # 提取時數
#         time_match = re.search(r"閱讀時數：(\d{1,3}:\d{2}:\d{2})", text)
#         if time_match: read_secs = _parse_read_seconds(time_match.group(1))
        
#         # 提取分數
#         score_match = re.search(r"測驗：(\d+)", text)
#         if score_match: exam_score = int(score_match.group(1))

#         log.info(f"📊 狀態檢查: 時數 {read_secs}/{int(threshold_secs)}s, 問卷: {'V' if survey_done else 'X'}, 分數: {exam_score}")

#         if read_secs < threshold_secs:
#             return "in_progress", read_secs
#         if not survey_done:
#             return "need_survey", read_secs
#         if exam_score < 60:
#             return "need_exam", read_secs
            
#         return "completed", read_secs
#     except:
#         return "unknown", 0

# def _parse_read_seconds(time_str: str) -> int:
#     try:
#         parts = time_str.split(":")
#         return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
#     except: return 0

# def _get_cert_hours(driver, index):
#     try:
#         cards = driver.find_elements(By.CSS_SELECTOR, "div.course-list-inner")
#         if index >= len(cards): return None
#         card_text = cards[index].text
#         match = re.search(r"認證時數\s*:\s*([\d.]+)", card_text)
#         return float(match.group(1)) if match else None
#     except: return None

# def _go_to_next_page(driver, wait) -> bool:
#     try:
#         next_btn = driver.find_element(By.CSS_SELECTOR, "i.paginate-next")
#         parent = next_btn.find_element(By.XPATH, "..")
#         if not parent.get_attribute("href") and not parent.get_attribute("title"):
#             return False
#         next_btn.click()
#         time.sleep(2)
#         return True
#     except: return False

# def _dismiss_notice_popup(driver):
#     try:
#         btn = driver.find_element(By.XPATH, "//button[contains(text(),'了解，我清楚了')]")
#         btn.click()
#         time.sleep(1)
#     except: pass

# def _watch_idle_thread(driver, idle_thread, stop_flag, index, check_interval=5, max_idle_secs=None):
#     from selenium.common.exceptions import UnexpectedAlertPresentException
#     start_time = time.time()
#     while idle_thread.is_alive():
#         time.sleep(check_interval)
#         elapsed = time.time() - start_time
#         if max_idle_secs and elapsed >= max_idle_secs:
#             stop_flag[0] = True
#             break
#         try:
#             _ = driver.current_url
#         except UnexpectedAlertPresentException:
#             stop_flag[0] = True
#             raise SessionExpiredError("Session Expired")
#         except:
#             stop_flag[0] = True
#             break

# if __name__ == "__main__":
#     from open_browser import open_browser
#     from login import login
#     driver = open_browser()
#     driver.get(config.BASE_URL)
#     if login(driver):
#         find_and_start_course(driver)
#     driver.quit()


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
from do_exam import do_exam  # 確保你有建立此檔案

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

PERSONAL_AREA_URL = "https://elearn.hrd.gov.tw/mooc/user/learn_dashboard.php"

class SessionExpiredError(Exception):
    """網站偵測到閒置並顯示 alert 強制登出時拋出。"""
    pass

def _relogin(driver: webdriver.Chrome) -> webdriver.Chrome:
    from open_browser import open_browser
    from login import login
    log.warning("🔄 帳號已被登出，準備重新開啟瀏覽器並登入...")
    try:
        driver.quit()
    except Exception:
        pass
    new_driver = open_browser()
    new_driver.get(config.BASE_URL)
    if not login(new_driver):
        raise RuntimeError("❌ 重新登入失敗，程式無法繼續")
    log.info("✅ 重新登入成功，繼續學習流程")
    return new_driver

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

def find_and_start_course(driver: webdriver.Chrome, stop_flag: list = None, _driver_box: list = None) -> bool:
    if stop_flag is None: stop_flag = [False]
    if _driver_box is None: _driver_box = [driver]
    else: _driver_box[0] = driver

    def _d() -> webdriver.Chrome: return _driver_box[0]
    def _w() -> WebDriverWait: return WebDriverWait(_d(), config.PAGE_LOAD_TIMEOUT)

    MAX_RELOGIN = 5
    relogin_count = 0

    while True:
        try:
            return _find_and_start_course_inner(_d, _w, stop_flag)
        except SessionExpiredError:
            relogin_count += 1
            if relogin_count > MAX_RELOGIN:
                log.error(f"❌ 已連續重登 {MAX_RELOGIN} 次仍失敗，放棄")
                return False
            try:
                new_driver = _relogin(_d())
                _driver_box[0] = new_driver
            except RuntimeError as e:
                log.error(str(e))
                return False

def _find_and_start_course_inner(_d, _w, stop_flag: list) -> bool:
    """
    新版流程：
    永遠只處理列表中的第一門課
    完成後課程會消失
    再繼續下一門
    """

    while True:

        # ---------------------------------------------------------
        # Step 1：回個人專區
        # ---------------------------------------------------------
        log.info("── 回到個人專區")

        _d().get(PERSONAL_AREA_URL + "?tab=1")

        time.sleep(2)

        _dismiss_notice_popup(_d())

        # ---------------------------------------------------------
        # Step 2：檢查是否還有課程
        # ---------------------------------------------------------
        try:

            _w().until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "img[alt='課程代表圖']")
                )
            )

            course_imgs = _d().find_elements(
                By.CSS_SELECTOR,
                "img[alt='課程代表圖']"
            )

        except TimeoutException:

            log.info("🏁 已無任何課程")
            return True

        # ---------------------------------------------------------
        # 沒課程
        # ---------------------------------------------------------
        if len(course_imgs) == 0:

            log.info("✅ 所有課程已完成")
            return True

        log.info(f"📚 剩餘課程數量: {len(course_imgs)}")

        # =========================================================
        # 永遠處理第一門
        # =========================================================
        try:

            # -----------------------------------------------------
            # 1. 取得認證時數
            # -----------------------------------------------------
            cert_hours = _get_cert_hours(_d(), 0)

            # -----------------------------------------------------
            # 2. 點第一門課
            # -----------------------------------------------------
            course_imgs[0].click()

            time.sleep(2)

            # -----------------------------------------------------
            # 3. 檢查課程狀態
            # -----------------------------------------------------
            status, read_secs = _is_already_completed(
                _d(),
                cert_hours
            )

            log.info(f"📊 目前課程狀態: {status}")

            # -----------------------------------------------------
            # 4. 如果未完成閱讀
            # -----------------------------------------------------
            if status == "in_progress":

                log.info("🚀 開始上課流程")

                _start_learning(
                    _d(),
                    _w(),
                    stop_flag,
                    cert_hours,
                    read_secs
                )

                time.sleep(2)

            # -----------------------------------------------------
            # 5. 填問卷
            # -----------------------------------------------------
            log.info("📝 開始填寫問卷")

            try:
                fill_questionnaire(_d())
            except Exception as e:
                log.warning(f"⚠️ 問卷填寫失敗: {e}")

            time.sleep(2)

            # -----------------------------------------------------
            # 6. 開始測驗
            # -----------------------------------------------------
            log.info("🤖 開始測驗流程")

            try:

                if _click(
                    _w(),
                    By.CSS_SELECTOR,
                    ".btnAction",
                    "點擊上課去"
                ):

                    time.sleep(3)

                    do_exam(_d())

            except Exception as e:

                log.error(f"❌ 測驗失敗: {e}")

            # -----------------------------------------------------
            # 7. 回列表
            # -----------------------------------------------------
            log.info("↩️ 返回課程列表")

            _d().get(PERSONAL_AREA_URL + "?tab=1")

            time.sleep(2)

        except SessionExpiredError:
            raise

        except Exception as e:

            log.error(f"❌ 課程處理失敗: {e}")

            try:
                _d().get(PERSONAL_AREA_URL + "?tab=1")
            except:
                pass

            time.sleep(2)


def _start_learning(driver, wait, stop_flag, cert_hours, read_secs) -> bool:
    """點擊上課去並執行防閒置"""
    try:
        goto_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btnAction")))
        goto_btn.click()
        time.sleep(3)
        
        # 計算需要防閒置的時間
        if cert_hours:
            max_idle_secs = max(0, int(cert_hours * 3600 * 0.53 - read_secs))
        else:
            max_idle_secs = 1800 # 預設 30 分鐘

        log.info(f"🔄 啟動防閒置，預計執行 {max_idle_secs} 秒")
        idle_interval = random.randint(600, 720) # 10-12 分鐘隨機
        
        stop_flag[0] = False
        idle_thread = threading.Thread(
            target=run_anti_idle_loop,
            args=(driver, idle_interval, stop_flag),
            daemon=True
        )
        idle_thread.start()
        
        # 監控
        _watch_idle_thread(driver, idle_thread, stop_flag, 0, max_idle_secs=max_idle_secs)
        return True
    except Exception as e:
        log.error(f"啟動學習失敗: {e}")
        return False

def _is_already_completed(driver, cert_hours, read_ratio: float = 0.5) -> tuple:
    """
    回傳 (status, read_secs)
    status: "completed", "need_survey", "need_exam", "in_progress"
    """
    if cert_hours is None: return "unknown", 0
    threshold_secs = cert_hours * 3600 * read_ratio

    try:
        status_div = driver.find_element(By.CSS_SELECTOR, "div.majorstatus")
        text = status_div.text.replace(" ", "")
        
        read_secs = 0
        survey_done = "已填" in text
        exam_score = 0
        
        # 提取時數
        time_match = re.search(r"閱讀時數：(\d{1,3}:\d{2}:\d{2})", text)
        if time_match: read_secs = _parse_read_seconds(time_match.group(1))
        
        # 提取分數
        score_match = re.search(r"測驗：(\d+)", text)
        if score_match: exam_score = int(score_match.group(1))

        log.info(f"📊 狀態檢查: 時數 {read_secs}/{int(threshold_secs)}s, 問卷: {'V' if survey_done else 'X'}, 分數: {exam_score}")

        if read_secs < threshold_secs:
            return "in_progress", read_secs
        if not survey_done:
            return "need_survey", read_secs
        if exam_score < 75:
            return "need_exam", read_secs
            
        return "completed", read_secs
    except:
        return "unknown", 0

def _parse_read_seconds(time_str: str) -> int:
    try:
        parts = time_str.split(":")
        return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
    except: return 0

def _get_cert_hours(driver, index):
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, "div.course-list-inner")
        if index >= len(cards): return None
        card_text = cards[index].text
        match = re.search(r"認證時數\s*:\s*([\d.]+)", card_text)
        return float(match.group(1)) if match else None
    except: return None

def _dismiss_notice_popup(driver):
    try:
        btn = driver.find_element(By.XPATH, "//button[contains(text(),'了解，我清楚了')]")
        btn.click()
        time.sleep(1)
    except: pass

def _watch_idle_thread(driver, idle_thread, stop_flag, index, check_interval=5, max_idle_secs=None):
    from selenium.common.exceptions import UnexpectedAlertPresentException
    start_time = time.time()
    while idle_thread.is_alive():
        time.sleep(check_interval)
        elapsed = time.time() - start_time
        if max_idle_secs and elapsed >= max_idle_secs:
            stop_flag[0] = True
            break
        try:
            _ = driver.current_url
        except UnexpectedAlertPresentException:
            stop_flag[0] = True
            raise SessionExpiredError("Session Expired")
        except:
            stop_flag[0] = True
            break

if __name__ == "__main__":
    from open_browser import open_browser
    from login import login
    driver = open_browser()
    driver.get(config.BASE_URL)
    if login(driver):
        find_and_start_course(driver)
    driver.quit()