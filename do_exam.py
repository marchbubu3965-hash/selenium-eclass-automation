
# import time
# import logging
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# log = logging.getLogger(__name__)

# def do_exam(driver):
#     """
#     1. 在 mooc_sysbar 點擊 測驗/考試
#     2. 在 s_main 點擊 進行測驗
#     3. 切換至新開啟的分頁 (分頁1)
#     """
#     wait = WebDriverWait(driver, 15)
    
#     # 紀錄點擊前的視窗句柄數量
#     old_windows = driver.window_handles

#     try:
#         # --- Step 1: 點擊左側選單 ---
#         driver.switch_to.default_content()
#         log.info("📡 嘗試切換至框架 [mooc_sysbar]...")
#         wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "mooc_sysbar")))
        
#         exam_link = wait.until(EC.element_to_be_clickable((By.ID, "SYS_04_02_002")))
#         driver.execute_script("arguments[0].click();", exam_link)
#         log.info("✅ 成功點擊「測驗/考試」！")

#         # --- Step 2: 點擊右側內容區的「進行測驗」 ---
#         time.sleep(2)
#         driver.switch_to.default_content()
#         log.info("🎯 切換至內容框架 [s_main]...")
#         wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "s_main")))

#         log.info("🔍 正在搜尋「進行測驗」按鈕...")
#         # 使用你提供的 class 進行定位
#         start_exam_btn = wait.until(EC.element_to_be_clickable(
#             (By.XPATH, "//div[contains(@class, 'main-text') and contains(text(), '進行測驗')]")
#         ))
        
#         driver.execute_script("arguments[0].click();", start_exam_btn)
#         log.info("✅ 已點擊「進行測驗」")

#         # --- Step 3: 切換到新分頁 ---
#         log.info("⏳ 等待新分頁開啟...")
        
#         # 等待視窗數量增加
#         wait.until(lambda d: len(d.window_handles) > len(old_windows))
        
#         # 取得所有視窗句柄
#         all_windows = driver.window_handles
#         # 通常新開啟的會在最後一個
#         new_window = all_windows[-1]
        
#         driver.switch_to.window(new_window)
#         log.info(f"🚩 控制權已移轉至新分頁：{driver.title}")
        
#         # 額外檢查：確保進入新頁面後不在任何 frame 裡
#         # driver.switch_to.default_content() 
        
#         return True

#     except Exception as e:
#         log.error(f"❌ 測驗流程執行失敗: {e}")
#         driver.save_screenshot("exam_flow_error.png")
#         return False

# if __name__ == "__main__":
#     pass
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

log = logging.getLogger(__name__)

def do_exam(driver):
    """
    1. 在 mooc_sysbar 點擊 測驗/考試
    2. 在 s_main 點擊 進行測驗
    3. 切換至新開啟的分頁 (分頁1)
    4. 點擊「開始作答」
    5. 提取 id="presentPanel" 內所有表格文字內容
    6. 關閉分頁並返回主視窗
    """
    wait = WebDriverWait(driver, 15)
    main_window = driver.current_window_handle
    old_windows = driver.window_handles

    try:
        # --- Step 1: 點擊左側選單 ---
        driver.switch_to.default_content()
        log.info("📡 嘗試切換至框架 [mooc_sysbar]...")
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "mooc_sysbar")))
        
        exam_link = wait.until(EC.element_to_be_clickable((By.ID, "SYS_04_02_002")))
        driver.execute_script("arguments[0].click();", exam_link)
        log.info("✅ 成功點擊「測驗/考試」！")

        # --- Step 2: 點擊右側內容區的「進行測驗」 ---
        time.sleep(2)
        driver.switch_to.default_content()
        log.info("🎯 切換至內容框架 [s_main]...")
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "s_main")))

        log.info("🔍 正在搜尋「進行測驗」按鈕...")
        start_exam_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@class, 'main-text') and contains(text(), '進行測驗')]")
        ))
        
        driver.execute_script("arguments[0].click();", start_exam_btn)
        log.info("✅ 已點擊「進行測驗」")

        # --- Step 3: 切換到新分頁 ---
        log.info("⏳ 等待新分頁開啟...")
        wait.until(lambda d: len(d.window_handles) > len(old_windows))
        new_window = driver.window_handles[-1]
        driver.switch_to.window(new_window)
        log.info(f"🚩 控制權已移轉至新分頁：{driver.title}")

        # --- Step 4: 點擊「開始作答」 ---
        log.info("⏳ 尋找「開始作答」按鈕...")
        start_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "input.cssBtn[value='開始作答']")
        ))
        start_btn.click()
        log.info("✅ 已點擊「開始作答」")

        # --- Step 5: 提取 id="presentPanel" 內的文字 ---
        log.info("⏳ 等待題目頁面載入 (id='presentPanel')...")
        # 確保 presentPanel 已載入
        wait.until(EC.presence_of_element_located((By.ID, "presentPanel")))
        time.sleep(2)  # 緩衝，確保表格內容完全呈現

        log.info("📝 正在提取 presentPanel 內的題目內容...")
        try:
            # 定位 presentPanel 元素
            present_panel = driver.find_element(By.ID, "presentPanel")
            # 取得該 Panel 內所有文字 (包含內部的表格文字)
            exam_text = present_panel.text
            
            print("\n" + "★" * 60)
            print("【 presentPanel 題目提取內容 】")
            print("★" * 60)
            print(exam_text)
            print("★" * 60 + "\n")
            
        except Exception as e:
            log.warning(f"⚠️ 提取 presentPanel 失敗: {e}")
            # 備援：如果抓不到特定的 Panel，抓取 responseForm 的文字
            try:
                print(driver.find_element(By.ID, "responseForm").text)
            except:
                log.error("❌ 無法提取任何題目文字")

        # --- Step 6: 結束並關閉 ---
        log.info("⌛ 提取完畢，等待 3 秒後關閉分頁...")
        time.sleep(3)
        
        driver.close()
        driver.switch_to.window(main_window)
        log.info("✅ 已關閉分頁並回到主視窗")
        
        return True

    except Exception as e:
        log.error(f"❌ 測驗流程執行失敗: {e}")
        driver.save_screenshot("exam_flow_error.png")
        # 發生錯誤時確保切換回主視窗
        if len(driver.window_handles) > 1:
            try:
                driver.close()
            except:
                pass
        driver.switch_to.window(main_window)
        return False

if __name__ == "__main__":
    pass