# import time
# import re
# import logging
# import threading

# # 💡 修正 1：改為標準的 Google GenAI SDK 引入方式與錯誤攔截
# import google.generativeai as genai
# from google.api_core.exceptions import ServiceUnavailable

# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# from selenium.common.exceptions import (
#     TimeoutException,
#     NoAlertPresentException
# )

# logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
# log = logging.getLogger(__name__)

# # =================================================================
# # 測驗鎖（避免多帳號同時測驗）
# # =================================================================
# EXAM_LOCK = threading.Lock()

# # =================================================================
# # Gemini API 設定
# # =================================================================
# GEMINI_API_KEY = "AIzaSyC-XAx7jprw4xITvNX_3ujde7Q_l2Kdj7U"

# # 💡 修正 2：使用最新標準的 configure 初始化方式
# genai.configure(api_key=GEMINI_API_KEY)

# # =================================================================
# # 答案映射
# # =================================================================
# ANSWER_MAP = {
#     "A": ["1"],
#     "B": ["2"],
#     "C": ["3"],
#     "D": ["4"],
#     "E": ["5"],

#     "O": ["T"],
#     "X": ["F"],

#     "T": ["T"],
#     "F": ["F"],
# }

# # =================================================================
# # Gemini 問答 (加入 503 自動重試機制)
# # =================================================================
# def ask_gemini(question_text, max_retries=5):
#     """
#     呼叫 Gemini 進行答題，並包含指數退避重試機制，防止 503 Service Unavailable 崩潰。
#     """
#     safe_text = str(question_text)
#     prompt = f"""
# 你是一個考試作答助手。

# 請根據以下題目直接輸出答案。

# 規則：
# 1. 只能輸出答案
# 2. 不要解釋
# 3. 格式範例：
# 單選或多選：
# 1.A
# 2.B
# 3.C
# 4.ABCD
# 是非題：
# 5.O
# 6.X

# 題目如下：

# {safe_text}
# """
    
#     # 💡 修正 3：改用標準的 GenerativeModel 初始化
#     model = genai.GenerativeModel("gemini-2.5-flash")
#     delay = 2  # 初始重試等待秒數

#     for attempt in range(max_retries):
#         try:
#             # 💡 修正 4：改用標準的 generate_content 呼叫語法
#             response = model.generate_content(prompt)
#             answer_text = response.text.strip()
#             return answer_text

#         except ServiceUnavailable:
#             # 💡 修正 5：精準捕捉 503 伺服器忙碌錯誤並執行自動重試
#             log.warning(f"⚠️ Gemini 伺服器忙碌中 (503)，將於 {delay} 秒後進行第 {attempt + 1} 次重試...")
#             time.sleep(delay)
#             delay *= 2  # 下一次等待時間加倍 (2s -> 4s -> 8s -> 16s)

#         except Exception as e:
#             # 其他非 503 錯誤（例如金鑰錯、格式錯）直接輸出 Log 並中斷
#             log.error(f"❌ Gemini API 發生未預期錯誤: {e}")
#             return ""

#     log.error("❌ 已達到最大重試次數，Gemini 伺服器持續忙碌中，放棄本次測驗作答。")
#     return ""

# # =================================================================
# # 解析 Gemini 回答
# # =================================================================
# def parse_answers(answer_text):
#     result = {}
#     if not answer_text:
#         return result

#     lines = answer_text.splitlines()
#     for line in lines:
#         line = line.strip().upper()
#         if not line:
#             continue

#         match = re.match(r"(\d+)\s*[\.\、\:]\s*([A-EXOTF]+)", line)
#         if not match:
#             continue

#         q_num = int(match.group(1))
#         answer_raw = match.group(2)

#         values = []
#         for ch in answer_raw:
#             if ch in ANSWER_MAP:
#                 values.extend(ANSWER_MAP[ch])

#         result[q_num] = values

#     return result

# # =================================================================
# # 自動勾選答案
# # =================================================================
# def auto_fill_answers(driver, parsed_answers):
#     questions = driver.find_elements(By.CSS_SELECTOR, "tr.bg03, tr.bg04")
#     log.info(f"📚 偵測到題目數量: {len(questions)}")

#     question_index = 0
#     for question in questions:
#         try:
#             inputs = question.find_elements(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
#             if not inputs:
#                 continue

#             question_index += 1
#             if question_index not in parsed_answers:
#                 log.warning(f"⚠️ 第 {question_index} 題沒有解析到答案")
#                 continue

#             answer_values = parsed_answers[question_index]
#             log.info(f"📝 第 {question_index} 題答案: {answer_values}")

#             for input_el in inputs:
#                 value = input_el.get_attribute("value")
#                 if value in answer_values:
#                     driver.execute_script("arguments[0].click();", input_el)
#                     log.info(f"✅ 第 {question_index} 題點選 value={value}")
#                     time.sleep(0.2)

#         except Exception as e:
#             log.error(f"❌ 第 {question_index} 題勾選失敗: {e}")

# # =================================================================
# # 送出答案
# # =================================================================
# def submit_exam(driver, wait):
#     try:
#         log.info("📤 準備送出答案")
#         submit_btn = wait.until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][value='送出答案，結束測驗']"))
#         )
#         driver.execute_script("arguments[0].click();", submit_btn)
#         log.info("✅ 已點擊送出按鈕")

#         # =========================================================
#         # Alert 確認
#         # =========================================================
#         try:
#             alert = WebDriverWait(driver, 10).until(EC.alert_is_present())
#             log.info(f"⚠️ Alert內容: {alert.text}")
#             alert.accept()
#             log.info("✅ 已點擊 Alert 確定")
#         except TimeoutException:
#             log.warning("⚠️ 未偵測到 Alert")
#         except NoAlertPresentException:
#             log.warning("⚠️ Alert 已消失")

#         time.sleep(5)
#         return True

#     except Exception as e:
#         log.error(f"❌ 送出答案失敗: {e}")
#         return False

# # =================================================================
# # 測驗流程
# # =================================================================
# def do_exam(driver):
#     with EXAM_LOCK:
#         log.info("🔒 已取得測驗鎖，開始測驗")
#         wait = WebDriverWait(driver, 15)

#         main_window = driver.current_window_handle
#         old_windows = driver.window_handles

#         try:
#             # =====================================================
#             # Step 1: 切換至選單框架
#             # =====================================================
#             driver.switch_to.default_content()
#             log.info("📡 切換至選單")
#             wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "mooc_sysbar")))

#             exam_link = wait.until(EC.element_to_be_clickable((By.ID, "SYS_04_02_002")))
#             driver.execute_script("arguments[0].click();", exam_link)

#             # =====================================================
#             # Step 2: 切換至主要內容框架並點擊進行測驗
#             # =====================================================
#             time.sleep(2)
#             driver.switch_to.default_content()
#             wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "s_main")))

#             start_exam_btn = wait.until(
#                 EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'main-text') and contains(text(),'進行測驗')]"))
#             )
#             driver.execute_script("arguments[0].click();", start_exam_btn)

#             # =====================================================
#             # Step 3: 等待並切換至彈出的新測驗分頁
#             # =====================================================
#             wait.until(lambda d: len(d.window_handles) > len(old_windows))
#             new_window = [w for w in driver.window_handles if w not in old_windows][0]
#             driver.switch_to.window(new_window)
#             log.info("✅ 已切換至測驗分頁")

#             # =====================================================
#             # Step 4: 點擊開始作答
#             # =====================================================
#             start_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.cssBtn[value='開始作答']")))
#             start_btn.click()

#             # =====================================================
#             # Step 5: 提取題目文字
#             # =====================================================
#             log.info("📝 正在提取題目")
#             wait.until(EC.presence_of_element_located((By.ID, "responseForm")))
#             time.sleep(2)

#             exam_table = driver.find_element(By.CSS_SELECTOR, "#responseForm")
#             exam_text = exam_table.text

#             # =====================================================
#             # Step 6: 諮詢 Gemini (內含自動重試機制)
#             # =====================================================
#             log.info("🤖 正在詢問 Gemini 2.5 Flash")
#             ai_answer = ask_gemini(exam_text)

#             print("\n" + "★" * 80)
#             print("🚀 【 Gemini 建議答案 】 🚀")
#             print("-" * 60)
#             print(ai_answer)
#             print("★" * 80 + "\n")

#             # =====================================================
#             # Step 7: 解析答案並自動勾選、送出
#             # =====================================================
#             parsed_answers = parse_answers(ai_answer)
#             log.info(f"📊 解析結果: {parsed_answers}")

#             auto_fill_answers(driver, parsed_answers)
#             submit_exam(driver, wait)

#             # =====================================================
#             # Step 10: 關閉分頁並還原主視窗
#             # =====================================================
#             log.info("🪟 關閉測驗分頁")
#             driver.close()
#             driver.switch_to.window(main_window)
#             log.info("✅ 已返回主頁")
#             return True

#         except Exception as e:
#             log.error(f"❌ 測驗流程錯誤: {e}")
#             try:
#                 if len(driver.window_handles) > 1:
#                     driver.close()
#             except:
#                 pass
#             try:
#                 driver.switch_to.window(main_window)
#             except:
#                 pass
#             return False

#         finally:
#             log.info("🔓 測驗結束，釋放測驗鎖")

# if __name__ == "__main__":
#     pass

import time
import re
import logging
import threading
import os

# 💡 修正 1：改為標準的 Google GenAI SDK 引入方式與錯誤攔截
import google.generativeai as genai
from google.api_core.exceptions import ServiceUnavailable

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import (
    TimeoutException,
    NoAlertPresentException
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# =================================================================
# 測驗鎖（避免多帳號同時測驗）
# =================================================================
EXAM_LOCK = threading.Lock()

# =================================================================
# Gemini API 設定（改為從 Accounts.txt 動態讀取，防止密鑰外洩至 GitHub）
# =================================================================
def load_gemini_api_key(filename="Accounts.txt"):
    """從 Accounts.txt 中動態讀取 GEMINI_API_KEY"""
    if not os.path.exists(filename):
        log.error(f"❌ 找不到設定檔 {filename}，無法讀取 API Key！")
        return None
        
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 忽略空白行與純註解行
                if not line or line.startswith("#"):
                    continue
                # 偵測 GEMINI_API_KEY=
                if line.startswith("GEMINI_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    log.info("✅ 成功從 Accounts.txt 讀取 Gemini API Key")
                    return key
    except Exception as e:
        log.error(f"❌ 讀取 {filename} 時發生錯誤: {e}")
        
    return None

# 動態載入 Key
GEMINI_API_KEY = load_gemini_api_key()

# 💡 使用最新標準的 configure 初始化方式
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    log.error("❌ 未能成功辨識 Gemini API Key，請檢查 Accounts.txt 是否設定正確。")

# =================================================================
# 答案映射
# =================================================================
ANSWER_MAP = {
    "A": ["1"],
    "B": ["2"],
    "C": ["3"],
    "D": ["4"],
    "E": ["5"],

    "O": ["T"],
    "X": ["F"],

    "T": ["T"],
    "F": ["F"],
}

# =================================================================
# Gemini 問答 (加入 503 自動重試機制)
# =================================================================
def ask_gemini(question_text, max_retries=5):
    """
    呼校 Gemini 進行答題，並包含指數退避重試機制，防止 503 Service Unavailable 崩潰。
    """
    if not GEMINI_API_KEY:
        log.error("❌ Gemini API Key 為空，無法執行問答！")
        return ""

    safe_text = str(question_text)
    prompt = f"""
你是一個考試作答助手。

請根據以下題目直接輸出答案。

規則：
1. 只能輸出答案
2. 不要解釋
3. 格式範例：
單選或多選：
1.A
2.B
3.C
4.ABCD
是非題：
5.O
6.X

題目如下：

{safe_text}
"""
    
    # 💡 修正 3：改用標準的 GenerativeModel 初始化
    model = genai.GenerativeModel("gemini-2.5-flash")
    delay = 2  # 初始重試等待秒數

    for attempt in range(max_retries):
        try:
            # 💡 修正 4：改用標準的 generate_content 呼叫語法
            response = model.generate_content(prompt)
            answer_text = response.text.strip()
            return answer_text

        except ServiceUnavailable:
            # 💡 修正 5：精準捕捉 503 伺服器忙碌錯誤並執行自動重試
            log.warning(f"⚠️ Gemini 伺服器忙碌中 (503)，將於 {delay} 秒後進行第 {attempt + 1} 次重試...")
            time.sleep(delay)
            delay *= 2  # 下一次等待時間加倍 (2s -> 4s -> 8s -> 16s)

        except Exception as e:
            # 其他非 503 錯誤（例如金鑰錯、格式錯）直接輸出 Log 並中斷
            log.error(f"❌ Gemini API 發生未預期錯誤: {e}")
            return ""

    log.error("❌ 已達到最大重試次數，Gemini 伺服器持續忙碌中，放棄本次測驗作答。")
    return ""

# =================================================================
# 解析 Gemini 回答
# =================================================================
def parse_answers(answer_text):
    result = {}
    if not answer_text:
        return result

    lines = answer_text.splitlines()
    for line in lines:
        line = line.strip().upper()
        if not line:
            continue

        match = re.match(r"(\d+)\s*[\.\、\:]\s*([A-EXOTF]+)", line)
        if not match:
            continue

        q_num = int(match.group(1))
        answer_raw = match.group(2)

        values = []
        for ch in answer_raw:
            if ch in ANSWER_MAP:
                values.extend(ANSWER_MAP[ch])

        result[q_num] = values

    return result

# =================================================================
# 自動勾選答案
# =================================================================
def auto_fill_answers(driver, parsed_answers):
    questions = driver.find_elements(By.CSS_SELECTOR, "tr.bg03, tr.bg04")
    log.info(f"📚 偵測到題目數量: {len(questions)}")

    question_index = 0
    for question in questions:
        try:
            inputs = question.find_elements(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
            if not inputs:
                continue

            question_index += 1
            if question_index not in parsed_answers:
                log.warning(f"⚠️ 第 {question_index} 題沒有解析到答案")
                continue

            answer_values = parsed_answers[question_index]
            log.info(f"📝 第 {question_index} 題答案: {answer_values}")

            for input_el in inputs:
                value = input_el.get_attribute("value")
                if value in answer_values:
                    driver.execute_script("arguments[0].click();", input_el)
                    log.info(f"✅ 第 {question_index} 題點選 value={value}")
                    time.sleep(0.2)

        except Exception as e:
            log.error(f"❌ 第 {question_index} 題勾選失敗: {e}")

# =================================================================
# 送出答案
# =================================================================
def submit_exam(driver, wait):
    try:
        log.info("📤 準備送出答案")
        submit_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][value='送出答案，結束測驗']"))
        )
        driver.execute_script("arguments[0].click();", submit_btn)
        log.info("✅ 已點擊送出按鈕")

        # =========================================================
        # Alert 確認
        # =========================================================
        try:
            alert = WebDriverWait(driver, 10).until(EC.alert_is_present())
            log.info(f"⚠️ Alert內容: {alert.text}")
            alert.accept()
            log.info("✅ 已點擊 Alert 確定")
        except TimeoutException:
            log.warning("⚠️ 未偵測到 Alert")
        except NoAlertPresentException:
            log.warning("⚠️ Alert 已消失")

        time.sleep(5)
        return True

    except Exception as e:
        log.error(f"❌ 送出答案失敗: {e}")
        return False

# =================================================================
# 測驗流程
# =================================================================
def do_exam(driver):
    with EXAM_LOCK:
        log.info("🔒 已取得測驗鎖，開始測驗")
        wait = WebDriverWait(driver, 15)

        main_window = driver.current_window_handle
        old_windows = driver.window_handles

        try:
            # =====================================================
            # Step 1: 切換至選單框架
            # =====================================================
            driver.switch_to.default_content()
            log.info("📡 切換至選單")
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "mooc_sysbar")))

            exam_link = wait.until(EC.element_to_be_clickable((By.ID, "SYS_04_02_002")))
            driver.execute_script("arguments[0].click();", exam_link)

            # =====================================================
            # Step 2: 切換至主要內容框架並點擊進行測驗
            # =====================================================
            time.sleep(2)
            driver.switch_to.default_content()
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "s_main")))

            start_exam_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'main-text') and contains(text(),'進行測驗')]"))
            )
            driver.execute_script("arguments[0].click();", start_exam_btn)

            # =====================================================
            # Step 3: 等待並切換至彈出的新測驗分頁
            # =====================================================
            wait.until(lambda d: len(d.window_handles) > len(old_windows))
            new_window = [w for w in driver.window_handles if w not in old_windows][0]
            driver.switch_to.window(new_window)
            log.info("✅ 已切換至測驗分頁")

            # =====================================================
            # Step 4: 點擊開始作答
            # =====================================================
            start_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.cssBtn[value='開始作答']")))
            start_btn.click()

            # =====================================================
            # Step 5: 提取題目文字
            # =====================================================
            log.info("📝 正在提取題目")
            wait.until(EC.presence_of_element_located((By.ID, "responseForm")))
            time.sleep(2)

            exam_table = driver.find_element(By.CSS_SELECTOR, "#responseForm")
            exam_text = exam_table.text

            # =====================================================
            # Step 6: 諮詢 Gemini (內含自動重試機制)
            # =====================================================
            log.info("🤖 正在詢問 Gemini 2.5 Flash")
            ai_answer = ask_gemini(exam_text)

            print("\n" + "★" * 80)
            print("🚀 【 Gemini 建議答案 】 🚀")
            print("-" * 60)
            print(ai_answer)
            print("★" * 80 + "\n")

            # =====================================================
            # Step 7: 解析答案並自動勾選、送出
            # =====================================================
            parsed_answers = parse_answers(ai_answer)
            log.info(f"📊 解析結果: {parsed_answers}")

            auto_fill_answers(driver, parsed_answers)
            submit_exam(driver, wait)

            # =====================================================
            # Step 10: 關閉分頁並還原主視窗
            # =====================================================
            log.info("🪟 關閉測驗分頁")
            driver.close()
            driver.switch_to.window(main_window)
            log.info("✅ 已返回主頁")
            return True

        except Exception as e:
            log.error(f"❌ 測驗流程錯誤: {e}")
            try:
                if len(driver.window_handles) > 1:
                    driver.close()
            except:
                pass
            try:
                driver.switch_to.window(main_window)
            except:
                pass
            return False

        finally:
            log.info("🔓 測驗結束，釋放測驗鎖")

if __name__ == "__main__":
    pass