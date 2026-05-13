"""
run_multi.py
同時以多個帳號執行 E等公務園自動學習流程。

用法：
    python run_multi.py                     # 跑 ACCOUNTS 清單內所有帳號
    python run_multi.py --workers 5         # 最多同時 5 個帳號
    python run_multi.py --headless          # 不顯示瀏覽器視窗
    python run_multi.py --max-hours 4       # 每個帳號最多 4 小時

帳號設定：
    直接修改下方 ACCOUNTS 清單，或建立 accounts.txt（每行一筆 帳號:密碼）。
"""

import sys
import os
import time
import logging
import argparse
import threading
import multiprocessing

# ── 確保能 import 同資料夾的模組 ──────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ══════════════════════════════════════════════════════════════════════
# 帳號清單：在這裡填入你的帳號密碼
# ══════════════════════════════════════════════════════════════════════
ACCOUNTS = [
    {"username": "account01", "password": "password01"},
    {"username": "account02", "password": "password02"},
    {"username": "account03", "password": "password03"},
    {"username": "account04", "password": "password04"},
    {"username": "account05", "password": "password05"},
    {"username": "account06", "password": "password06"},
    {"username": "account07", "password": "password07"},
    {"username": "account08", "password": "password08"},
    {"username": "account09", "password": "password09"},
    {"username": "account10", "password": "password10"},
]


# ══════════════════════════════════════════════════════════════════════
# 單一帳號的完整流程（在 subprocess 內執行）
# ══════════════════════════════════════════════════════════════════════
def run_single_account(username: str, password: str, headless: bool, max_hours: float):
    """
    在獨立的 Process 中跑一個帳號的完整流程。
    每個 Process 有自己的 Chrome，互不干擾。
    """
    import config
    from open_browser          import open_browser
    from login                 import login
    from find_and_start_course import find_and_start_course
    from anti_idle             import run_anti_idle_loop

    # 用 username 區隔 log 前綴
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [{username}] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger(username)

    log.info(f"▶ 帳號 {username} 開始執行")
    driver = open_browser(headless=headless)

    try:
        # 登入
        if not login(driver, username=username, password=password):
            log.error("登入失敗，結束此帳號")
            return

        # 找課程並開始上課
        if not find_and_start_course(driver):
            log.error("無法進入課程，結束此帳號")
            return

        # 防閒置 + 時間上限
        stop_flag = [False]
        max_secs  = max_hours * 3600

        idle_thread = threading.Thread(
            target=run_anti_idle_loop,
            args=(driver, config.ANTI_IDLE_INTERVAL, stop_flag),
            daemon=True,
            name=f"AntiIdle-{username}",
        )
        idle_thread.start()
        log.info(f"⏳ 學習中... 最長 {max_hours} 小時")

        start_time = time.time()
        while not stop_flag[0]:
            if time.time() - start_time >= max_secs:
                log.warning(f"⏰ 達到最大學習時間 {max_hours} 小時，結束")
                stop_flag[0] = True
            time.sleep(5)

        idle_thread.join(timeout=5)

    except KeyboardInterrupt:
        log.info("手動中止")
    except Exception as e:
        log.error(f"發生未預期錯誤：{e}")
    finally:
        log.info("關閉瀏覽器")
        try:
            driver.quit()
        except Exception:
            pass
        log.info(f"✅ 帳號 {username} 結束")


# ══════════════════════════════════════════════════════════════════════
# 讀取外部帳號檔（可選）
# ══════════════════════════════════════════════════════════════════════
def load_accounts_from_file(filepath: str) -> list:
    """
    從文字檔讀取帳號，格式：每行一筆 帳號:密碼
    例如：
        wazxd941202:Wazxd810644..
        account02:password02
    """
    accounts = []
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":", 1)
            if len(parts) == 2:
                accounts.append({"username": parts[0], "password": parts[1]})
            else:
                print(f"[警告] 無法解析帳號行：{line}")
    return accounts


# ══════════════════════════════════════════════════════════════════════
# 主程式：控制並行數量
# ══════════════════════════════════════════════════════════════════════
MAX_CONCURRENT = 10  # 同時執行上限，不需手動調整

def main():
    parser = argparse.ArgumentParser(description="E等公務園 多帳號同時學習")
    parser.add_argument("--headless",  action="store_true",      help="不顯示瀏覽器視窗")
    parser.add_argument("--max-hours", type=float, default=8.0,  help="每個帳號最長學習時數（預設 8）")
    parser.add_argument("--accounts",  type=str,   default="",   help="帳號檔路徑（accounts.txt），留空使用程式內 ACCOUNTS 清單")
    args = parser.parse_args()

    # 決定帳號來源
    accounts_file = args.accounts or (
        "accounts.txt" if os.path.exists("accounts.txt") else ""
    )
    if accounts_file:
        accounts = load_accounts_from_file(accounts_file)
        print(f"📋 從 {accounts_file} 讀取 {len(accounts)} 個帳號")
    else:
        accounts = ACCOUNTS
        print(f"📋 使用程式內建帳號清單，共 {len(accounts)} 個帳號")

    if not accounts:
        print("❌ 沒有帳號可執行，請設定 ACCOUNTS 清單或提供 accounts.txt")
        return

    # 自動決定並行數：帳號有幾組就跑幾組，上限 MAX_CONCURRENT
    workers   = min(len(accounts), MAX_CONCURRENT)
    headless  = args.headless
    max_hours = args.max_hours

    print(f"🚀 偵測到 {len(accounts)} 組帳號，同時啟動 {workers} 個")
    print(f"   headless={headless}, max_hours={max_hours}")
    print("=" * 60)

    # 用 multiprocessing.Pool 控制並行數
    # 每個 process 完全獨立，有自己的 Chrome 和記憶體空間
    pool_args = [
        (acc["username"], acc["password"], headless, max_hours)
        for acc in accounts
    ]

    # 手動控制：一次最多 workers 個 Process，前一批結束才啟動下一批
    active_procs = []

    for i, kwargs in enumerate(pool_args):
        # 等候直到有空位
        while len(active_procs) >= workers:
            active_procs = [p for p in active_procs if p.is_alive()]
            time.sleep(3)

        username = kwargs[0]
        p = multiprocessing.Process(
            target=run_single_account,
            args=kwargs,
            name=f"Worker-{username}",
        )
        p.start()
        active_procs.append(p)
        print(f"[{i+1}/{len(pool_args)}] 啟動帳號：{username} (PID {p.pid})")
        # 錯開啟動時間，避免同時大量開啟瀏覽器造成系統卡頓
        time.sleep(5)

    # 等待所有 Process 結束
    print("\n⏳ 等待所有帳號完成...")
    for p in active_procs:
        p.join()

    print("\n✅ 所有帳號執行完畢")


if __name__ == "__main__":
    # Windows 需要這行才能正確使用 multiprocessing
    multiprocessing.freeze_support()
    main()