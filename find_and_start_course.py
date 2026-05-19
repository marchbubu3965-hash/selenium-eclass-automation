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
# from do_exam import do_exam 

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
#     """
#     新版分頁判斷流程：
#     1. 在列表頁只抓「認證時數」
#     2. 點進課程圖示後，在課程內頁的「我的課程狀態」判斷閱讀時數、問卷、測驗
#     """
#     current_index = 0  # 從第一門課開始檢查

#     while True:
#         # ---------------------------------------------------------
#         # Step 1：回個人專區 (課程列表頁)
#         # ---------------------------------------------------------
#         log.info("── 回到個人專區列表頁")
#         _d().get(PERSONAL_AREA_URL + "?tab=1")
#         time.sleep(2)
#         _dismiss_notice_popup(_d())

#         # ---------------------------------------------------------
#         # Step 2：檢查是否還有課程圖示
#         # ---------------------------------------------------------
#         try:
#             _w().until(
#                 EC.presence_of_element_located((By.CSS_SELECTOR, "img[alt='課程代表圖']"))
#             )
#             course_imgs = _d().find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
#         except TimeoutException:
#             log.info("🏁 已無任何課程")
#             return True

#         if len(course_imgs) == 0:
#             log.info("✅ 所有課程已完成")
#             return True

#         if current_index >= len(course_imgs):
#             log.info("🎉 列表中所有課程皆已檢查/處理完畢！程式結束。")
#             return True

#         # =========================================================
#         # 階段一：在【列表頁】僅判斷認證時數，並點擊進入
#         # =========================================================
#         try:
#             log.info(f"🔍 [列表頁] 正在檢查第 {current_index + 1} 門課程的認證時數...")
            
#             # 1. 僅在外層取得認證時數
#             cert_hours = _get_cert_hours(_d(), current_index)
#             if cert_hours is None:
#                 log.warning(f"⚠️ 無法取得第 {current_index + 1} 門課的認證時數，跳下一門。")
#                 current_index += 1
#                 continue
                
#             log.info(f"📐 認證時數: {cert_hours} 小時 (目標閱讀需達 {cert_hours * 0.5} 小時)")

#             # 2. 直接點擊圖示進入課程內頁
#             course_imgs[current_index].click()
#             time.sleep(3)  # 等待進入內頁

#             # =========================================================
#             # 階段二：在【課程內頁】判斷閱讀時數、問卷、測驗
#             # =========================================================
#             status, read_secs = _check_inner_page_status(_d(), cert_hours)
#             log.info(f"📊 課程內頁狀態判定結果: {status}")

#             if status == "completed":
#                 log.info(f"⏭️ 本課程已達標 (時數夠、問卷已填、且已測驗過)，自動跳到下一門。")
#                 current_index += 1  # 往下檢查下一門
#                 continue

#             # 根據內頁判定的狀態，精準執行對應動作
#             if status == "in_progress":
#                 log.info("🚀 [分流 1] 閱讀時數不足，開始上課流程...")
#                 _start_learning(_d(), _w(), stop_flag, cert_hours, read_secs)
#                 time.sleep(2)

#             elif status == "need_survey":
#                 log.info("📝 [分流 2] 時數足夠但問卷未填，開始填寫問卷...")
#                 try:
#                     fill_questionnaire(_d())
#                 except Exception as e:
#                     log.warning(f"⚠️ 問卷填寫失敗: {e}")
#                 time.sleep(2)

#             elif status == "need_exam":
#                 log.info("🤖 [分流 3] 時數與問卷已OK，且尚未測驗，開始測驗流程...")
#                 try:
#                     if _click(_w(), By.CSS_SELECTOR, ".btnAction", "點擊上課去"):
#                         time.sleep(3)
#                         do_exam(_d())
#                 except Exception as e:
#                     log.error(f"❌ 測驗失敗: {e}")

#             # 處理完這門課的目前需求後，重置回到第 1 門重新檢視
#             current_index = 0 

#         except SessionExpiredError:
#             raise
#         except Exception as e:
#             log.error(f"❌ 課程處理失敗: {e}")
#             current_index += 1  # 發生未知錯誤時跳過這門，避免無窮死迴圈
#             time.sleep(2)


# def _check_inner_page_status(driver, cert_hours: float, read_ratio: float = 0.5) -> tuple:
#     """
#     【全新設計】在課程內頁中，尋找「我的課程狀態」區塊並解析：
#     1. 閱讀時數是否 >= 認證時數的一半
#     2. 有的話，繼續判斷問卷是否已填
#     3. 有的話，最後判斷測驗欄位是否有數字
#     """
#     threshold_secs = cert_hours * 3600 * read_ratio
    
#     try:
#         # 💡 使用 XPath 精準定位包含「我的課程狀態」的 span 標籤
#         # 並一併等待它的父層或周圍的狀態區塊加載出來
#         status_span = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '我的課程狀態')]"))
#         )
        
#         # 向上尋找包含完整狀態資訊的容器文字（通常是整張狀態表格或大區塊）
#         # 這裡我們直接抓取 span 附近、或是整個內頁主體文字來比對
#         container_element = driver.find_element(By.XPATH, "//span[contains(text(), '我的課程狀態')]/ancestor::div[1] | //body")
#         text = container_element.text.replace(" ", "")
        
#         read_secs = 0
#         survey_done = "已填" in text
        
#         # 1. 提取目前的閱讀時數
#         time_match = re.search(r"閱讀時數：(\d{1,3}:\d{2}:\d{2})", text)
#         if time_match: 
#             read_secs = _parse_read_seconds(time_match.group(1))
#             log.info(f"⏱️ 內頁偵測到目前閱讀時數: {time_match.group(1)} ({read_secs}秒)")
#         else:
#             log.warning("⚠️ 內頁文字中找不到『閱讀時數：』格式，預設為 0 秒")

#         # 💡 【判斷 1】 判斷閱讀時數是否小於「認證時數的一半」
#         if read_secs < threshold_secs:
#             return "in_progress", read_secs

#         # 💡 【判斷 2】 時數夠了，繼續判斷問卷：未填 -> 填寫問卷
#         if not survey_done:
#             return "need_survey", read_secs

#         # 💡 【判斷 3】 時數夠、問卷已填，判斷測驗是否有數字
#         score_match = re.search(r"測驗：(\d+)", text)
#         if score_match:
#             # 有找到任何數字（不管是 0 還是 50 還是 100），代表已測驗過 -> 跳下一門课
#             log.info(f"ℹ️ 測驗欄位已有分數 ({score_match.group(1)})，不重複測驗。")
#             return "completed", read_secs  
#         else:
#             # 沒數字（顯示 測驗：--）-> 去測驗
#             log.info("ℹ️ 測驗欄位無數字(顯示--)，準備進入測驗。")
#             return "need_exam", read_secs
            
#     except Exception as e:
#         log.error(f"❌ 解析內頁課程狀態失敗: {e}")
#         # 如果找不到元件，保守回傳 in_progress 讓程式嘗試點擊上課去
#         return "in_progress", 0

# # 以下為原程式碼保留未改動部分 -----------------------------------------

# def _start_learning(driver, wait, stop_flag, cert_hours, read_secs) -> bool:
#     """點擊上課去並執行防閒置"""
#     try:
#         read_ratio = 0.5
#         if cert_hours:
#             max_idle_secs = max(0, int(cert_hours * 3600 * read_ratio + 150 - read_secs))
#         else:
#             max_idle_secs = 1800 

#         if max_idle_secs <= 0:
#             log.info("🎯 偵測到目前閱讀時數已達標，不需啟動防閒置，直接跳過上課流程。")
#             return True

#         goto_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btnAction")))
#         goto_btn.click()
#         time.sleep(3)

#         log.info(f"🔄 啟動防閒置，預計執行 {max_idle_secs} 秒")
#         idle_interval = random.randint(600, 720) 
        
#         stop_flag[0] = False
#         idle_thread = threading.Thread(
#             target=run_anti_idle_loop,
#             args=(driver, idle_interval, stop_flag),
#             daemon=True
#         )
#         idle_thread.start()
        
#         _watch_idle_thread(driver, idle_thread, stop_flag, 0, max_idle_secs=max_idle_secs)
#         return True
#     except Exception as e:
#         log.error(f"啟動學習失敗: {e}")
#         return False

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
from do_exam import do_exam 

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
    新版分頁判斷流程：
    1. 在列表頁只抓「認證時數」
    2. 點進課程圖示後，在課程內頁的「我的課程狀態」判斷閱讀時數、問卷、測驗
    """
    current_index = 0  # 從第一門課開始檢查

    while True:
        # ---------------------------------------------------------
        # Step 1：回個人專區 (課程列表頁)
        # ---------------------------------------------------------
        log.info("── 回到個人專區列表頁")
        _d().get(PERSONAL_AREA_URL + "?tab=1")
        time.sleep(2)
        _dismiss_notice_popup(_d())

        # ---------------------------------------------------------
        # Step 2：檢查是否還有課程圖示
        # ---------------------------------------------------------
        try:
            _w().until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img[alt='課程代表圖']"))
            )
            course_imgs = _d().find_elements(By.CSS_SELECTOR, "img[alt='課程代表圖']")
        except TimeoutException:
            log.info("🏁 已無任何課程")
            return True

        if len(course_imgs) == 0:
            log.info("✅ 所有課程已完成")
            return True

        if current_index >= len(course_imgs):
            log.info("🎉 列表中所有課程皆已檢查/處理完畢！程式結束。")
            return True

        # =========================================================
        # 階段一：在【列表頁】僅判斷認證時數，並點擊進入
        # =========================================================
        try:
            log.info(f"🔍 [列表頁] 正在檢查第 {current_index + 1} 門課程的認證時數...")
            
            # 1. 僅在外層取得認證時數
            cert_hours = _get_cert_hours(_d(), current_index)
            if cert_hours is None:
                log.warning(f"⚠️ 無法取得第 {current_index + 1} 門課的認證時數，跳下一門。")
                current_index += 1
                continue
                
            log.info(f"📐 認證時數: {cert_hours} 小時 (目標閱讀需達 {cert_hours * 0.5} 小時)")

            # 2. 直接點擊圖示進入課程內頁
            course_imgs[current_index].click()
            time.sleep(3)  # 等待進入內頁

            # =========================================================
            # 階段二：在【課程內頁】判斷閱讀時數、問卷、測驗
            # =========================================================
            status, read_secs = _check_inner_page_status(_d(), cert_hours)
            log.info(f"📊 課程內頁狀態判定結果: {status}")

            if status == "completed":
                log.info(f"⏭️ 本課程已達標 (時數夠、問卷已填、且已測驗過)，自動跳到下一門。")
                current_index += 1  # 往下檢查下一門
                continue

            # 根據內頁判定的狀態，精準執行對應動作
            if status == "in_progress":
                log.info("🚀 [分流 1] 閱讀時數不足，開始上課流程...")
                _start_learning(_d(), _w(), stop_flag, cert_hours, read_secs)
                time.sleep(2)

            elif status == "need_survey":
                log.info("📝 [分流 2] 時數足夠但問卷未填，先點上課去再填寫問卷...")
                try:
                    if _click(_w(), By.CSS_SELECTOR, ".btnAction", "點擊上課去"):
                        time.sleep(3)
                        fill_questionnaire(_d())
                except Exception as e:
                    log.warning(f"⚠️ 問卷填寫失敗: {e}")
                time.sleep(2)

            elif status == "need_exam":
                log.info("🤖 [分流 3] 時數與問卷已OK，且尚未測驗，開始測驗流程...")
                try:
                    if _click(_w(), By.CSS_SELECTOR, ".btnAction", "點擊上課去"):
                        time.sleep(3)
                        do_exam(_d())
                except Exception as e:
                    log.error(f"❌ 測驗失敗: {e}")

            # 處理完這門課的目前需求後，重置回到第 1 門重新檢視
            current_index = 0 

        except SessionExpiredError:
            raise
        except Exception as e:
            log.error(f"❌ 課程處理失敗: {e}")
            current_index += 1  # 發生未知錯誤時跳過這門，避免無窮死迴圈
            time.sleep(2)


def _check_inner_page_status(driver, cert_hours: float, read_ratio: float = 0.5) -> tuple:
    """
    【全新設計】在課程內頁中，尋找「我的課程狀態」區塊並解析：
    1. 閱讀時數是否 >= 認證時數的一半
    2. 有的話，繼續判斷問卷是否已填
    3. 有的話，最後判斷測驗欄位是否有數字
    """
    threshold_secs = cert_hours * 3600 * read_ratio
    
    try:
        # 💡 使用 XPath 精準定位包含「我的課程狀態」的 span 標籤
        # 並一併等待它的父層或周圍的狀態區塊加載出來
        status_span = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '我的課程狀態')]"))
        )
        
        # 向上尋找包含完整狀態資訊的容器文字（通常是整張狀態表格或大區塊）
        # 這裡我們直接抓取 span 附近、或是整個內頁主體文字來比對
        container_element = driver.find_element(By.XPATH, "//span[contains(text(), '我的課程狀態')]/ancestor::div[1] | //body")
        text = container_element.text.replace(" ", "")
        
        read_secs = 0
        survey_done = "已填" in text
        
        # 1. 提取目前的閱讀時數
        time_match = re.search(r"閱讀時數：(\d{1,3}:\d{2}:\d{2})", text)
        if time_match: 
            read_secs = _parse_read_seconds(time_match.group(1))
            log.info(f"⏱️ 內頁偵測到目前閱讀時數: {time_match.group(1)} ({read_secs}秒)")
        else:
            log.warning("⚠️ 內頁文字中找不到『閱讀時數：』格式，預設為 0 秒")

        # 💡 【判斷 1】 判斷閱讀時數是否小於「認證時數的一半」
        if read_secs < threshold_secs:
            return "in_progress", read_secs

        # 💡 【判斷 2】 時數夠了，繼續判斷問卷：未填 -> 填寫問卷
        if not survey_done:
            return "need_survey", read_secs

        # 💡 【判斷 3】 時數夠、問卷已填，判斷測驗是否有數字
        score_match = re.search(r"測驗：(\d+)", text)
        if score_match:
            # 有找到任何數字（不管是 0 還是 50 還是 100），代表已測驗過 -> 跳下一門课
            log.info(f"ℹ️ 測驗欄位已有分數 ({score_match.group(1)})，不重複測驗。")
            return "completed", read_secs  
        else:
            # 沒數字（顯示 測驗：--）-> 去測驗
            log.info("ℹ️ 測驗欄位無數字(顯示--)，準備進入測驗。")
            return "need_exam", read_secs
            
    except Exception as e:
        log.error(f"❌ 解析內頁課程狀態失敗: {e}")
        # 如果找不到元件，保守回傳 in_progress 讓程式嘗試點擊上課去
        return "in_progress", 0

# 以下為原程式碼保留未改動部分 -----------------------------------------

def _start_learning(driver, wait, stop_flag, cert_hours, read_secs) -> bool:
    """點擊上課去並執行防閒置"""
    try:
        read_ratio = 0.5
        if cert_hours:
            max_idle_secs = max(0, int(cert_hours * 3600 * read_ratio + 180 - read_secs))
        else:
            max_idle_secs = 1800 

        if max_idle_secs <= 0:
            log.info("🎯 偵測到目前閱讀時數已達標，不需啟動防閒置，直接跳過上課流程。")
            return True

        goto_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btnAction")))
        goto_btn.click()
        time.sleep(3)

        log.info(f"🔄 啟動防閒置，預計執行 {max_idle_secs} 秒")
        idle_interval = random.randint(600, 720) 
        
        stop_flag[0] = False
        idle_thread = threading.Thread(
            target=run_anti_idle_loop,
            args=(driver, idle_interval, stop_flag),
            daemon=True
        )
        idle_thread.start()
        
        _watch_idle_thread(driver, idle_thread, stop_flag, 0, max_idle_secs=max_idle_secs)
        return True
    except Exception as e:
        log.error(f"啟動學習失敗: {e}")
        return False

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