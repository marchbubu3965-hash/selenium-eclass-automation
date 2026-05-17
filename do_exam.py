

# import time
# import re
# import logging
# import os

# from google import genai

# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# log = logging.getLogger(__name__)

# # =================================================================
# # Gemini API 設定
# # =================================================================
# GEMINI_API_KEY = "AIzaSyCUTWVn-WdA1dsyarNyuyNmZKbacdeS7fQ"

# os.environ["PYTHONIOENCODING"] = "utf-8"
# client = genai.Client(
#     api_key=GEMINI_API_KEY
# )

# # =================================================================
# # Gemini 問答
# # =================================================================
# # =================================================================
# # Gemini 問答
# # =================================================================
# def ask_gemini(question_text):

#     try:

#         prompt = f"""
# {question_text}

# 請直接給答案。

# 格式範例：
# 單選或多選：
# 1.A
# 2.B
# 3.C
# 4.ABCD
# 是非題：
# 5.O
# 6.X

# 不要解釋。
# """

#         response = client.models.generate_content(
#             model="gemini-2.5-flash",
#             contents=prompt
#         )

#         # 避免 None
#         if not response.text:
#             return "❌ Gemini 無回應"

#         answer = str(response.text).strip()

#         return answer

#     except Exception as e:

#         log.error(f"❌ Gemini API 錯誤: {repr(e)}")

#         return f"❌ Gemini API 錯誤: {repr(e)}"

# # =================================================================
# # 解析 Gemini 答案
# # =================================================================
# def parse_answers(answer_text):

#     """
#     將 Gemini 回答解析成：

#     {
#         1: ["A"],
#         2: ["B", "C"],
#         3: ["O"],
#         4: ["X"]
#     }
#     """

#     result = {}

#     lines = answer_text.splitlines()

#     for line in lines:

#         line = line.strip()

#         if not line:
#             continue

#         match = re.match(
#             r"(\d+)\s*[\.\、]?\s*([A-EXO]+)",
#             line,
#             re.IGNORECASE
#         )

#         if not match:
#             continue

#         q_num = int(match.group(1))

#         answers = list(
#             match.group(2).upper()
#         )

#         result[q_num] = answers

#     return result

# # =================================================================
# # 自動勾選答案
# # =================================================================
# # =================================================================
# # 自動勾選答案
# # =================================================================
# def auto_select_answers(driver, answers_dict):

#     answer_map = {
#         "A": "1",
#         "B": "2",
#         "C": "3",
#         "D": "4",
#         "E": "5",
#         "O": "T",
#         "X": "F"
#     }

#     # =============================================================
#     # 抓所有題目列
#     # =============================================================
#     question_rows = driver.find_elements(
#         By.CSS_SELECTOR,
#         "tr.bg03, tr.bg04"
#     )

#     log.info(f"📚 找到 {len(question_rows)} 題")

#     for q_num, answers in answers_dict.items():

#         try:

#             # 題號從 1 開始
#             row = question_rows[q_num - 1]

#             log.info(
#                 f"📝 第 {q_num} 題 -> {answers}"
#             )

#             for ans in answers:

#                 value = answer_map.get(ans)

#                 if not value:
#                     continue

#                 try:

#                     option = row.find_element(
#                         By.CSS_SELECTOR,
#                         f"input[value='{value}']"
#                     )

#                     # 避免重複點擊
#                     if not option.is_selected():

#                         # 捲動到元素
#                         driver.execute_script(
#                             "arguments[0].scrollIntoView({block:'center'});",
#                             option
#                         )

#                         time.sleep(0.2)

#                         # 點擊
#                         driver.execute_script(
#                             "arguments[0].click();",
#                             option
#                         )

#                         log.info(
#                             f"✅ 第 {q_num} 題選擇 {ans}"
#                         )

#                         time.sleep(0.3)

#                 except Exception as e:

#                     log.error(
#                         f"❌ 第 {q_num} 題選項 {ans} 點擊失敗: {e}"
#                     )

#         except Exception as e:

#             log.error(
#                 f"❌ 找不到第 {q_num} 題: {e}"
#             )

# # =================================================================
# # 測驗流程
# # =================================================================
# def do_exam(driver):

#     """
#     測驗自動化流程
#     """

#     wait = WebDriverWait(driver, 15)

#     main_window = driver.current_window_handle

#     old_windows = driver.window_handles

#     try:

#         # =========================================================
#         # Step 1: 切換至選單
#         # =========================================================
#         driver.switch_to.default_content()

#         log.info("📡 切換至選單...")

#         wait.until(
#             EC.frame_to_be_available_and_switch_to_it(
#                 (By.NAME, "mooc_sysbar")
#             )
#         )

#         exam_link = wait.until(
#             EC.element_to_be_clickable(
#                 (By.ID, "SYS_04_02_002")
#             )
#         )

#         driver.execute_script(
#             "arguments[0].click();",
#             exam_link
#         )

#         # =========================================================
#         # Step 2: 點擊進行測驗
#         # =========================================================
#         time.sleep(2)

#         driver.switch_to.default_content()

#         wait.until(
#             EC.frame_to_be_available_and_switch_to_it(
#                 (By.NAME, "s_main")
#             )
#         )

#         start_exam_btn = wait.until(
#             EC.element_to_be_clickable(
#                 (
#                     By.XPATH,
#                     "//div[contains(@class, 'main-text') and contains(text(), '進行測驗')]"
#                 )
#             )
#         )

#         driver.execute_script(
#             "arguments[0].click();",
#             start_exam_btn
#         )

#         # =========================================================
#         # Step 3: 切換測驗分頁
#         # =========================================================
#         wait.until(
#             lambda d:
#             len(d.window_handles) > len(old_windows)
#         )

#         driver.switch_to.window(
#             driver.window_handles[-1]
#         )

#         # =========================================================
#         # Step 4: 開始作答
#         # =========================================================
#         start_btn = wait.until(
#             EC.element_to_be_clickable(
#                 (
#                     By.CSS_SELECTOR,
#                     "input.cssBtn[value='開始作答']"
#                 )
#             )
#         )

#         start_btn.click()

#         # =========================================================
#         # Step 5: 擷取題目
#         # =========================================================
#         log.info("📝 正在提取題目...")

#         wait.until(
#             EC.presence_of_element_located(
#                 (By.ID, "presentPanel")
#             )
#         )

#         time.sleep(2)

#         exam_text = driver.find_element(
#             By.ID,
#             "presentPanel"
#         ).text

#         # =========================================================
#         # Step 6: 問 Gemini
#         # =========================================================
#         log.info("🤖 正在詢問 Gemini 2.5 Flash...")

#         ai_answer = ask_gemini(exam_text)

#         print("\n" + "★" * 60)
#         print("🚀 【 Gemini 建議答案 】 🚀")
#         print("-" * 60)
#         print(ai_answer)
#         print("★" * 60 + "\n")

#         # =========================================================
#         # Step 7: 解析答案
#         # =========================================================
#         answers_dict = parse_answers(ai_answer)

#         log.info(f"📊 解析結果: {answers_dict}")

#         # =========================================================
#         # Step 8: 自動勾選答案
#         # =========================================================
#         auto_select_answers(
#             driver,
#             answers_dict
#         )

#         # =========================================================
#         # Step 9: 檢查是否所有題目都有作答
#         # =========================================================
#         log.info("🔍 檢查是否所有題目已作答...")

#         question_rows = driver.find_elements(
#             By.CSS_SELECTOR,
#             "tr.bg03, tr.bg04"
#         )

#         all_answered = True

#         for idx, row in enumerate(question_rows, start=1):

#             try:

#                 checked = row.find_elements(
#                     By.CSS_SELECTOR,
#                     "input:checked"
#                 )

#                 if len(checked) == 0:

#                     log.warning(f"⚠️ 第 {idx} 題尚未作答")

#                     all_answered = False

#             except:
#                 pass

#         # =========================================================
#         # Step 10: 自動送出答案
#         # =========================================================
#         if all_answered:

#             log.info("🚀 所有題目已作答，準備送出答案")

#             try:

#                 submit_btn = driver.find_element(
#                     By.CSS_SELECTOR,
#                     "input[value='送出答案，結束測驗']"
#                 )

#                 # 捲動到底部
#                 driver.execute_script(
#                     "arguments[0].scrollIntoView({block:'center'});",
#                     submit_btn
#                 )

#                 time.sleep(1)

#                 # 點擊送出
#                 driver.execute_script(
#                     "arguments[0].click();",
#                     submit_btn
#                 )

#                 log.info("✅ 已送出答案")

#                 time.sleep(5)

#             except Exception as e:

#                 log.error(f"❌ 送出答案失敗: {e}")

#         else:

#             log.warning("⚠️ 有題目未作答，取消自動交卷")

#         # =========================================================
#         # Step 11: 關閉測驗頁
#         # =========================================================
#         try:

#             driver.close()

#         except:
#             pass

#         # =========================================================
#         # Step 12: 回主視窗
#         # =========================================================
#         driver.switch_to.window(main_window)

#         log.info("↩️ 已返回主頁面")

#         return True

#     except Exception as e:

#         log.error(f"❌ 測驗流程錯誤: {e}")

#         try:

#             if len(driver.window_handles) > 1:
#                 driver.close()

#         except:
#             pass

#         try:
#             driver.switch_to.window(main_window)
#         except:
#             pass

#         return False

# # =================================================================
# # Main
# # =================================================================
# if __name__ == "__main__":

#     pass

import time
import re
import logging
import threading

from google import genai

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import (
    TimeoutException,
    NoAlertPresentException
)

log = logging.getLogger(__name__)

# =================================================================
# 測驗鎖（避免多帳號同時測驗）
# =================================================================
EXAM_LOCK = threading.Lock()

# =================================================================
# Gemini API 設定
# =================================================================
GEMINI_API_KEY = "AIzaSyCUTWVn-WdA1dsyarNyuyNmZKbacdeS7fQ"

client = genai.Client(
    api_key=GEMINI_API_KEY
)

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
# Gemini 問答
# =================================================================
def ask_gemini(question_text):

    try:

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

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer_text = response.text.strip()

        return answer_text

    except Exception as e:

        log.error(f"❌ Gemini API 錯誤: {e}")

        return ""

# =================================================================
# 解析 Gemini 回答
# =================================================================
def parse_answers(answer_text):

    result = {}

    lines = answer_text.splitlines()

    for line in lines:

        line = line.strip().upper()

        if not line:
            continue

        match = re.match(
            r"(\d+)\s*[\.\、\:]\s*([A-EXOTF]+)",
            line
        )

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

    questions = driver.find_elements(
        By.CSS_SELECTOR,
        "tr.bg03, tr.bg04"
    )

    log.info(f"📚 偵測到題目數量: {len(questions)}")

    question_index = 0

    for question in questions:

        try:

            inputs = question.find_elements(
                By.CSS_SELECTOR,
                "input[type='radio'], input[type='checkbox']"
            )

            if not inputs:
                continue

            question_index += 1

            if question_index not in parsed_answers:

                log.warning(
                    f"⚠️ 第 {question_index} 題沒有解析到答案"
                )

                continue

            answer_values = parsed_answers[question_index]

            log.info(
                f"📝 第 {question_index} 題答案: {answer_values}"
            )

            for input_el in inputs:

                value = input_el.get_attribute("value")

                if value in answer_values:

                    driver.execute_script(
                        "arguments[0].click();",
                        input_el
                    )

                    log.info(
                        f"✅ 第 {question_index} 題點選 value={value}"
                    )

                    time.sleep(0.2)

        except Exception as e:

            log.error(
                f"❌ 第 {question_index} 題勾選失敗: {e}"
            )

# =================================================================
# 送出答案
# =================================================================
def submit_exam(driver, wait):

    try:

        log.info("📤 準備送出答案")

        submit_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "input[type='submit'][value='送出答案，結束測驗']"
                )
            )
        )

        driver.execute_script(
            "arguments[0].click();",
            submit_btn
        )

        log.info("✅ 已點擊送出按鈕")

        # =========================================================
        # Alert 確認
        # =========================================================
        try:

            alert = WebDriverWait(driver, 10).until(
                EC.alert_is_present()
            )

            log.info(f"⚠️ Alert內容: {alert.text}")

            alert.accept()

            log.info("✅ 已點擊 Alert 確定")

        except TimeoutException:

            log.warning("⚠️ 未偵測到 Alert")

        except NoAlertPresentException:

            log.warning("⚠️ Alert 已消失")

        # =========================================================
        # 等待送出完成
        # =========================================================
        time.sleep(5)

        return True

    except Exception as e:

        log.error(f"❌ 送出答案失敗: {e}")

        return False

# =================================================================
# 測驗流程
# =================================================================
def do_exam(driver):

    # =============================================================
    # 測驗鎖
    # =============================================================
    with EXAM_LOCK:

        log.info("🔒 已取得測驗鎖，開始測驗")

        wait = WebDriverWait(driver, 15)

        main_window = driver.current_window_handle
        old_windows = driver.window_handles

        try:

            # =====================================================
            # Step 1
            # =====================================================
            driver.switch_to.default_content()

            log.info("📡 切換至選單")

            wait.until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.NAME, "mooc_sysbar")
                )
            )

            exam_link = wait.until(
                EC.element_to_be_clickable(
                    (By.ID, "SYS_04_02_002")
                )
            )

            driver.execute_script(
                "arguments[0].click();",
                exam_link
            )

            # =====================================================
            # Step 2
            # =====================================================
            time.sleep(2)

            driver.switch_to.default_content()

            wait.until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.NAME, "s_main")
                )
            )

            start_exam_btn = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[contains(@class,'main-text') and contains(text(),'進行測驗')]"
                    )
                )
            )

            driver.execute_script(
                "arguments[0].click();",
                start_exam_btn
            )

            # =====================================================
            # Step 3
            # =====================================================
            wait.until(
                lambda d:
                len(d.window_handles) > len(old_windows)
            )

            # 改良版抓新分頁（避免多帳號抓錯）
            new_window = [
                w for w in driver.window_handles
                if w not in old_windows
            ][0]

            driver.switch_to.window(new_window)

            log.info("✅ 已切換至測驗分頁")

            # =====================================================
            # Step 4
            # =====================================================
            start_btn = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "input.cssBtn[value='開始作答']"
                    )
                )
            )

            start_btn.click()

            # =====================================================
            # Step 5
            # =====================================================
            log.info("📝 正在提取題目")

            wait.until(
                EC.presence_of_element_located(
                    (By.ID, "responseForm")
                )
            )

            time.sleep(2)

            exam_table = driver.find_element(
                By.CSS_SELECTOR,
                "#responseForm"
            )

            exam_text = exam_table.text

            # =====================================================
            # Step 6
            # =====================================================
            log.info("🤖 正在詢問 Gemini 2.5 Flash")

            ai_answer = ask_gemini(exam_text)

            print("\n" + "★" * 80)
            print("🚀 【 Gemini 建議答案 】 🚀")
            print("-" * 60)
            print(ai_answer)
            print("★" * 80 + "\n")

            # =====================================================
            # Step 7
            # =====================================================
            parsed_answers = parse_answers(ai_answer)

            log.info(f"📊 解析結果: {parsed_answers}")

            # =====================================================
            # Step 8
            # =====================================================
            auto_fill_answers(
                driver,
                parsed_answers
            )

            # =====================================================
            # Step 9
            # =====================================================
            submit_exam(
                driver,
                wait
            )

            # =====================================================
            # Step 10
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

# =================================================================
# Main
# =================================================================
if __name__ == "__main__":
    pass