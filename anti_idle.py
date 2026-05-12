# """
# 4_anti_idle.py
# 功能：定時模擬使用者互動，防止網站閒置偵測踢下線。
#       可單獨呼叫 anti_idle()，或執行 run_anti_idle_loop() 持續運作。
# """

# import time
# import random
# import logging
# from selenium import webdriver
# from selenium.common.exceptions import WebDriverException

# import config

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
# )
# log = logging.getLogger(__name__)


# # ══════════════════════════════════════════
# # 單次防閒置動作
# # ══════════════════════════════════════════
# def anti_idle(driver: webdriver.Chrome):
#     """
#     執行一次防閒置動作：
#       1. 隨機小幅滾動頁面
#       2. 觸發滑鼠移動事件
#       3. 確保 <video> 持續播放
#       4. 處理 iframe 內的影片
#     """
#     try:
#         # 1. 小幅隨機滾動
#         scroll_y = random.randint(-80, 80)
#         driver.execute_script(f"window.scrollBy(0, {scroll_y});")

#         # 2. 模擬滑鼠移動
#         driver.execute_script("""
#             document.dispatchEvent(new MouseEvent('mousemove', {
#                 bubbles: true,
#                 cancelable: true,
#                 clientX: Math.random() * window.innerWidth,
#                 clientY: Math.random() * window.innerHeight
#             }));
#         """)

#         # 3. 主頁面影片持續播放
#         driver.execute_script("""
#             document.querySelectorAll('video').forEach(function(v) {
#                 if (v.paused && !v.ended) {
#                     v.play().catch(function(){});
#                 }
#             });
#         """)

#         # 4. iframe 內影片
#         _handle_iframes(driver)

#         log.info(f"🖱️  防閒置完成（頁面滾動 {scroll_y:+d}px）")

#     except WebDriverException as e:
#         log.warning(f"防閒置時 WebDriver 發生問題：{e}")
#     except Exception as e:
#         log.warning(f"防閒置發生未預期錯誤：{e}")


# def _handle_iframes(driver: webdriver.Chrome):
#     """切入每個 iframe，確保影片播放並觸發互動事件。"""
#     try:
#         iframes = driver.find_elements("tag name", "iframe")
#     except Exception:
#         return

#     for iframe in iframes:
#         try:
#             driver.switch_to.frame(iframe)
#             driver.execute_script("""
#                 // 影片繼續播放
#                 document.querySelectorAll('video').forEach(function(v) {
#                     if (v.paused && !v.ended) { v.play().catch(function(){}); }
#                 });
#                 // 觸發互動事件（部分 SCORM 課程依賴此事件計算時間）
#                 document.dispatchEvent(new MouseEvent('mousemove', {bubbles: true}));
#                 document.dispatchEvent(new Event('click', {bubbles: true}));
#             """)
#         except Exception:
#             pass
#         finally:
#             driver.switch_to.default_content()


# # ══════════════════════════════════════════
# # 持續防閒置迴圈（供外部呼叫）
# # ══════════════════════════════════════════
# def run_anti_idle_loop(
#     driver: webdriver.Chrome,
#     interval: int = config.ANTI_IDLE_INTERVAL,
#     stop_flag: list = None,
# ):
#     """
#     每隔 interval 秒執行一次 anti_idle()，直到 stop_flag[0] == True。

#     Args:
#         driver:    已開啟的 Chrome WebDriver。
#         interval:  防閒置間隔（秒），預設取 config.ANTI_IDLE_INTERVAL。
#         stop_flag: 傳入 [False]，當外部設定 stop_flag[0] = True 時停止迴圈。
#                    留空則永久執行（Ctrl+C 中止）。
#     """
#     if stop_flag is None:
#         stop_flag = [False]

#     log.info(f"🔄 防閒置迴圈啟動（每 {interval} 秒執行一次）")
#     last_action = 0.0

#     while not stop_flag[0]:
#         now = time.time()
#         if now - last_action >= interval:
#             anti_idle(driver)
#             last_action = now
#         time.sleep(1)

#     log.info("防閒置迴圈已停止")


# # ── 單獨執行測試 ──────────────────────────
# if __name__ == "__main__":
#     from open_browser import open_browser
#     from login import login

#     driver = open_browser()
#     if login(driver):
#         log.info("開始單獨測試防閒置（Ctrl+C 可中止）...")
#         try:
#             run_anti_idle_loop(driver, interval=config.ANTI_IDLE_INTERVAL)
#         except KeyboardInterrupt:
#             log.info("手動中止")
#     driver.quit()

"""
4_anti_idle.py
功能：定時模擬使用者互動，防止網站閒置偵測踢下線。
      可單獨呼叫 anti_idle()，或執行 run_anti_idle_loop() 持續運作。
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════
# 單次防閒置動作
# ══════════════════════════════════════════
def anti_idle(driver: webdriver.Chrome):
    """
    執行一次防閒置動作：
      1. 滑鼠移動至 (300, 130) 並左鍵點擊
      2. 等待 2 秒
      3. 滑鼠移動至 (300, 150) 並左鍵點擊
    """
    try:
        time.sleep(3)

        # 1. 移動至 (300, 130) 並點擊
        actions = ActionChains(driver)
        actions.move_by_offset(300, 130).click()
        actions.perform()
        log.info("🖱️  滑鼠點擊 (300, 130) 完成")
        # 重設位置
        ActionChains(driver).move_by_offset(-300, -130).perform()

        time.sleep(2)

        # 2. 移動至 (300, 150) 並點擊
        actions = ActionChains(driver)
        actions.move_by_offset(300, 150).click()
        actions.perform()
        log.info("🖱️  滑鼠點擊 (300, 150) 完成")
        # 重設位置
        ActionChains(driver).move_by_offset(-300, -150).perform()

    except WebDriverException as e:
        log.warning(f"防閒置時 WebDriver 發生問題：{e}")
    except Exception as e:
        log.warning(f"防閒置發生未預期錯誤：{e}")


# ══════════════════════════════════════════
# 持續防閒置迴圈（供外部呼叫）
# ══════════════════════════════════════════
def run_anti_idle_loop(
    driver: webdriver.Chrome,
    interval: int = config.ANTI_IDLE_INTERVAL,
    stop_flag: list = None,
):
    """
    每隔 interval 秒執行一次 anti_idle()，直到 stop_flag[0] == True。

    Args:
        driver:    已開啟的 Chrome WebDriver。
        interval:  防閒置間隔（秒），預設取 config.ANTI_IDLE_INTERVAL。
        stop_flag: 傳入 [False]，當外部設定 stop_flag[0] = True 時停止迴圈。
                   留空則永久執行（Ctrl+C 中止）。
    """
    if stop_flag is None:
        stop_flag = [False]

    log.info(f"🔄 防閒置迴圈啟動（每 {interval} 秒執行一次）")
    last_action = 0.0

    while not stop_flag[0]:
        now = time.time()
        if now - last_action >= interval:
            anti_idle(driver)
            last_action = now
        time.sleep(1)

    log.info("防閒置迴圈已停止")


# ── 單獨執行測試 ──────────────────────────
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from open_browser import open_browser
    from login import login

    driver = open_browser()
    if login(driver):
        log.info("開始單獨測試防閒置（Ctrl+C 可中止）...")
        try:
            run_anti_idle_loop(driver, interval=config.ANTI_IDLE_INTERVAL)
        except KeyboardInterrupt:
            log.info("手動中止")
    driver.quit()