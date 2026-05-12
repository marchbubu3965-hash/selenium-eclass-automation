"""
2_login.py
功能：接收 driver，依照 E等公務園實際登入流程，完成以下 7 個步驟：
  Step 1. 點擊首頁「登入」按鈕（開啟彈窗）
  Step 2. 點擊「了解，我清楚了」確認按鈕
  Step 3. 點擊「我的e政府」選項
  Step 4. 點擊「登入我的e政府」按鈕
  Step 5. 點擊「我的E政府帳號登入」
  Step 6. 輸入帳號與密碼
  Step 7. 點擊「登入」送出
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def _click(wait: WebDriverWait, by, selector: str, desc: str) -> bool:
    """等待元素可點擊後點擊，成功回傳 True，逾時回傳 False。"""
    try:
        el = wait.until(EC.element_to_be_clickable((by, selector)))
        el.click()
        log.info(f"✅ {desc}")
        time.sleep(1.5)
        return True
    except TimeoutException:
        log.error(f"❌ 逾時找不到：{desc}（selector: {selector}）")
        return False


def _dismiss_notice_button(driver: webdriver.Chrome, timeout: int = 2):
    """
    偵測「了解，我清楚了」按鈕是否存在，存在才點擊，沒有則靜默略過。
    同時支援 id="targetloginButtonArea" 及文字比對兩種方式。
    """
    selectors = [
        (By.ID, "targetloginButtonArea"),
        (By.XPATH, "//button[contains(text(),'了解，我清楚了')]"),
        # (By.XPATH, "//button[contains(text(),'我清楚了')]"),
        # (By.XPATH, "//a[contains(text(),'了解，我清楚了')]"),
    ]
    short_wait = WebDriverWait(driver, timeout)
    for by, selector in selectors:
        try:
            btn = short_wait.until(EC.element_to_be_clickable((by, selector)))
            btn.click()
            log.info("✅ 已點擊「了解，我清楚了」")
            time.sleep(1.5)
            return
        except TimeoutException:
            continue
        except Exception as e:
            log.warning(f"點擊「了解，我清楚了」時發生問題：{e}")
            continue

    log.info("ℹ️  未偵測到「了解，我清楚了」視窗，繼續執行")


def _switch_to_fancybox_iframe(driver: webdriver.Chrome):
    """
    嘗試切換進入 fancybox 彈窗的 iframe。
    找不到則維持在主頁面。
    """
    try:
        iframe = WebDriverWait(driver, 1.5).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "#fancybox-frame, iframe.fancybox-iframe, "
                ".fancybox-inner iframe, iframe[src*='login'], "
                "iframe[src*='gov_login'], iframe[src*='dialog'], "
                "iframe[src*='co_login']"
            ))
        )
        driver.switch_to.frame(iframe)
        log.info("已切換進入 fancybox iframe")
    except TimeoutException:
        log.info("未偵測到 fancybox iframe，維持在主頁面")


def login(
    driver: webdriver.Chrome,
    username: str = config.USERNAME,
    password: str = config.PASSWORD,
) -> bool:
    """
    依照 E等公務園實際 7 步驟流程完成登入。

    Returns:
        True 表示登入成功，False 表示任一步驟失敗。
    """
    wait = WebDriverWait(driver, config.PAGE_LOAD_TIMEOUT)

    try:
        # ── Step 1：點擊首頁「登入」按鈕 ────────────────────────────
        # <a id="login_md" class="login-btn" href="/mooc/co_login_dialog.php">登入</a>
        log.info("── Step 1：點擊首頁「登入」按鈕")
        if not _click(wait, By.ID, "login_md", "已點擊「登入」"):
            driver.save_screenshot("step1_failed.png")
            return False

        # ── Step 2：點擊「了解，我清楚了」（可選，有才點） ──────────
        # <button id="targetloginButtonArea">了解，我清楚了</button>
        # 按鈕在 fancybox iframe 內，部分情況下不會出現
        log.info("── Step 2：偵測「了解，我清楚了」視窗")
        _switch_to_fancybox_iframe(driver)
        _dismiss_notice_button(driver)

        # ── Step 3：點擊「我的e政府」 ───────────────────────────────
        # <a href="/mooc/co_gov_login_guide.php?identity=1" class="gov_btn">我的e政府</a>
        log.info("── Step 3：點擊「我的e政府」")
        if not _click(
            wait,
            By.CSS_SELECTOR,
            "a[href*='co_gov_login_guide.php'][class*='gov_btn'], "
            "a.gov_btn[href*='identity=1']",
            "已點擊「我的e政府」",
        ):
            driver.switch_to.default_content()
            driver.save_screenshot("step3_failed.png")
            return False

        # ── Step 4：點擊「登入我的e政府」 ──────────────────────────
        # <button class="btn btn-lg btn-block btn-orange gov-btn">登入我的e政府</button>
        log.info("── Step 4：點擊「登入我的e政府」")
        driver.switch_to.default_content()
        _switch_to_fancybox_iframe(driver)
        if not _click(
            wait,
            By.CSS_SELECTOR,
            "button.btn-orange.gov-btn, button.gov-btn.btn-orange",
            "已點擊「登入我的e政府」",
        ):
            driver.switch_to.default_content()
            driver.save_screenshot("step4_failed.png")
            return False

        # ── Step 5：點擊「我的E政府帳號登入」 ─────────────────────
        # <a id="accountlinkbt" class="btn btnlogin">我的E政府帳號登入</a>
        # 此時可能已跳轉至外部「我的e政府」頁面
        log.info("── Step 5：點擊「我的E政府帳號登入」")
        driver.switch_to.default_content()
        time.sleep(2)  # 等頁面跳轉

        # 先嘗試主頁面，再嘗試 iframe
        found = _click(wait, By.ID, "accountlinkbt", "（主頁面）已點擊「我的E政府帳號登入」")
        if not found:
            _switch_to_fancybox_iframe(driver)
            found = _click(wait, By.ID, "accountlinkbt", "（iframe）已點擊「我的E政府帳號登入」")
        if not found:
            driver.save_screenshot("step5_failed.png")
            return False

        # ── Step 6：輸入帳號與密碼 ──────────────────────────────────
        # input id="AccountPassword_simple_txt_account"
        # input id="AccountPassword_simple_txt_password"
        log.info("── Step 6：輸入帳號與密碼")
        driver.switch_to.default_content()
        time.sleep(2)  # 等帳密表單載入
        _switch_to_fancybox_iframe(driver)

        # 帳號欄
        user_field = wait.until(
            EC.presence_of_element_located(
                (By.ID, "AccountPassword_simple_txt_account")
            )
        )
        user_field.clear()
        user_field.send_keys(username)
        log.info("已輸入帳號")
        time.sleep(0.5)

        # 密碼欄
        pass_field = driver.find_element(
            By.ID, "AccountPassword_simple_txt_password"
        )
        pass_field.clear()
        pass_field.send_keys(password)
        log.info("已輸入密碼")
        time.sleep(0.5)

        # ── Step 7：點擊「登入」送出 ────────────────────────────────
        log.info("── Step 7：點擊「登入」送出")
        found = _click(
            wait,
            By.CSS_SELECTOR,
            "input[type='submit'], button[type='submit'], input[type='image']",
            "已點擊登入送出按鈕",
        )
        if not found:
            # 備援：用文字 XPath 找
            try:
                btn = driver.find_element(
                    By.XPATH,
                    "//*[self::button or self::input or self::a]"
                    "[contains(text(),'登入') or @value='登入']"
                )
                btn.click()
                log.info("✅ （XPath備援）已點擊登入")
            except NoSuchElementException:
                driver.save_screenshot("step7_failed.png")
                return False

        # ── 等待回到 E等公務園並確認登入成功 ───────────────────────
        driver.switch_to.default_content()
        log.info("等待登入完成並跳轉回 E等公務園...")
        wait.until(
            EC.any_of(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".logout, .user-info, #user-menu, .member-name, .loginout")
                ),
                EC.url_contains("elearn.hrd.gov.tw"),
            )
        )

        log.info("✅ 登入成功！")

        # ── 登入後：關閉可能彈出的通知視窗 ─────────────────────────
        close_popups(driver)

        return True

    except TimeoutException as e:
        log.error(f"❌ 登入流程逾時：{e}")
        driver.save_screenshot("login_timeout.png")
        return False

    except Exception as e:
        log.error(f"❌ 登入時發生未預期錯誤：{e}")
        driver.save_screenshot("login_error.png")
        return False

    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def close_popups(driver: webdriver.Chrome, timeout: int = 5):
    """
    偵測並關閉登入後可能彈出的通知視窗（fancybox 彈窗）。
    判斷方式（命中任一即嘗試關閉）：
      1. 出現 #learn-contain-wrap（學習提醒彈窗）
      2. 出現 fancybox 關閉按鈕 .fancybox-close-small
      3. 出現 .fancybox-content 彈窗內容
    關閉方式依序嘗試：
      a. 點擊 fancybox 關閉按鈕
      b. 按下 ESC 鍵
      c. 用 JavaScript 移除彈窗 DOM
    """
    from selenium.webdriver.common.keys import Keys

    # 等一下，讓彈窗有時間跳出
    time.sleep(2)

    # 偵測彈窗是否存在
    popup_selectors = [
        "#learn-contain-wrap",          # 學習提醒彈窗（今年認證時數）
        ".fancybox-content",            # 任何 fancybox 內容
        ".fancybox-container",          # fancybox 容器
    ]

    popup_found = False
    for sel in popup_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            visible = [el for el in elements if el.is_displayed()]
            if visible:
                popup_found = True
                log.info(f"偵測到彈窗：{sel}（共 {len(visible)} 個）")
                break
        except Exception:
            continue

    if not popup_found:
        log.info("未偵測到登入後彈窗，繼續執行")
        return

    # ── 關閉方式 a：點擊 fancybox 關閉按鈕 ──────────────────────────
    close_selectors = [
        "button.fancybox-close-small",          # HTML 中的 ✕ 按鈕
        "button[data-fancybox-close]",           # data 屬性關閉按鈕
        ".fancybox-button--close",               # 另一種關閉樣式
        "button[title='Close']",                 # title="Close"
        ".fancybox-close",                       # 通用關閉 class
    ]

    closed = False
    for sel in close_selectors:
        try:
            btns = driver.find_elements(By.CSS_SELECTOR, sel)
            visible_btns = [b for b in btns if b.is_displayed()]
            if visible_btns:
                visible_btns[0].click()
                log.info(f"✅ 已點擊關閉按鈕關閉彈窗（{sel}）")
                time.sleep(1)
                closed = True
                break
        except Exception:
            continue

    # ── 關閉方式 b：按 ESC ───────────────────────────────────────────
    if not closed:
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            log.info("✅ 已按 ESC 關閉彈窗")
            time.sleep(1)
            closed = True
        except Exception as e:
            log.warning(f"ESC 關閉失敗：{e}")

    # ── 關閉方式 c：JavaScript 強制移除 ─────────────────────────────
    if not closed:
        try:
            driver.execute_script("""
                // 移除 fancybox 相關 DOM
                var selectors = [
                    '.fancybox-container',
                    '.fancybox-overlay',
                    '#fancybox-overlay',
                    '#learn-contain-wrap'
                ];
                selectors.forEach(function(sel) {
                    document.querySelectorAll(sel).forEach(function(el) {
                        el.remove();
                    });
                });
                // 還原 body overflow（fancybox 開啟時會鎖住捲動）
                document.body.style.overflow = '';
                document.documentElement.style.overflow = '';
            """)
            log.info("✅ 已用 JavaScript 強制移除彈窗")
            time.sleep(0.5)
        except Exception as e:
            log.warning(f"JavaScript 移除彈窗失敗：{e}")

    # 最終確認彈窗是否消失
    try:
        remaining = driver.find_elements(By.CSS_SELECTOR, ".fancybox-container")
        visible_remaining = [el for el in remaining if el.is_displayed()]
        if visible_remaining:
            log.warning("⚠️  彈窗可能仍存在，繼續執行後續流程")
        else:
            log.info("✅ 彈窗已成功關閉")
    except Exception:
        pass

    # ── 第二輪：偵測並關閉「最新消息」彈窗 ─────────────────────────
    _close_news_popup(driver)


def _close_news_popup(driver: webdriver.Chrome):
    """
    偵測頁面是否出現含有 <h2>最新消息</h2> 的彈窗，
    若有則嘗試關閉。
    """
    from selenium.webdriver.common.keys import Keys

    time.sleep(1)  # 等第一個彈窗關閉動畫結束，讓第二個有機會出現

    # ── 偵測「最新消息」標題是否可見 ────────────────────────────────
    news_found = False
    try:
        h2_list = driver.find_elements(By.XPATH, "//h2[contains(text(),'最新消息')]")
        visible_h2 = [el for el in h2_list if el.is_displayed()]
        if visible_h2:
            news_found = True
            log.info("偵測到「最新消息」彈窗")
    except Exception:
        pass

    if not news_found:
        log.info("未偵測到「最新消息」彈窗")
        return

    closed = False

    # ── 關閉方式 a：找彈窗內的關閉按鈕 ─────────────────────────────
    # 先找包含「最新消息」的父容器，再在容器內找關閉按鈕
    close_selectors = [
        "button.fancybox-close-small",
        "button[data-fancybox-close]",
        "button[title='Close']",
        ".fancybox-button--close",
        ".fancybox-close",
        ".modal-close",
        "button.close",
        "[aria-label='Close']",
    ]

    for sel in close_selectors:
        try:
            btns = driver.find_elements(By.CSS_SELECTOR, sel)
            visible_btns = [b for b in btns if b.is_displayed()]
            if visible_btns:
                visible_btns[0].click()
                log.info(f"✅ 已點擊關閉按鈕關閉「最新消息」（{sel}）")
                time.sleep(1)
                closed = True
                break
        except Exception:
            continue

    # ── 關閉方式 b：按 ESC ───────────────────────────────────────────
    if not closed:
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            log.info("✅ 已按 ESC 關閉「最新消息」彈窗")
            time.sleep(1)
            closed = True
        except Exception as e:
            log.warning(f"ESC 關閉「最新消息」失敗：{e}")

    # ── 關閉方式 c：JavaScript 強制移除包含「最新消息」的彈窗容器 ───
    if not closed:
        try:
            driver.execute_script("""
                // 找到含有「最新消息」文字的 h2，向上找最近的彈窗容器移除
                var h2s = document.querySelectorAll('h2');
                h2s.forEach(function(h2) {
                    if (h2.textContent.includes('最新消息')) {
                        // 向上尋找 fancybox 容器或 modal 容器
                        var parent = h2.closest(
                            '.fancybox-container, .fancybox-content, ' +
                            '.modal, .popup, [class*="dialog"]'
                        );
                        if (parent) {
                            parent.remove();
                        } else {
                            // 找不到容器就直接隱藏 h2 的上層區塊
                            h2.parentElement.style.display = 'none';
                        }
                    }
                });
                // 還原 body overflow
                document.body.style.overflow = '';
                document.documentElement.style.overflow = '';
            """)
            log.info("✅ 已用 JavaScript 強制移除「最新消息」彈窗")
            time.sleep(0.5)
        except Exception as e:
            log.warning(f"JavaScript 移除「最新消息」失敗：{e}")

    # ── 最終確認 ─────────────────────────────────────────────────────
    try:
        h2_list = driver.find_elements(By.XPATH, "//h2[contains(text(),'最新消息')]")
        still_visible = [el for el in h2_list if el.is_displayed()]
        if still_visible:
            log.warning("⚠️  「最新消息」彈窗可能仍存在，繼續執行後續流程")
        else:
            log.info("✅ 「最新消息」彈窗已成功關閉")
    except Exception:
        pass


# ── 單獨執行測試 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from open_browser import open_browser

    driver = open_browser()
    driver.get(config.BASE_URL)
    success = login(driver)
    if success:
        input("登入成功！按 Enter 關閉瀏覽器...")
    else:
        input("登入失敗，按 Enter 關閉（截圖已儲存）...")
    driver.quit()