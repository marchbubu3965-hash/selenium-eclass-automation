
"""
run_multi.py
同時以多個帳號執行 E等公務園自動學習流程。

用法：
    python run_multi.py              # 跑 ACCOUNTS 清單內所有帳號
    python run_multi.py --headless   # 不顯示瀏覽器視窗

帳號設定：
    直接修改下方 ACCOUNTS 清單，或建立 accounts.txt（每行一筆 帳號:密碼）。
"""

import sys
import os
import time
import logging
import argparse
import multiprocessing

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

STAGGER_SECONDS = 15  # 每組帳號啟動間隔（秒）
MAX_CONCURRENT  = 10  # 同時執行上限


# ══════════════════════════════════════════════════════════════════════
# 單一帳號的完整流程（在獨立 Process 內執行）
# ══════════════════════════════════════════════════════════════════════
def run_single_account(username: str, password: str, headless: bool):
    """
    find_and_start_course 會跑完所有課程後才返回，
    返回後直接關閉瀏覽器，不設時間上限。
    """
    from open_browser          import open_browser
    from login                 import login
    from find_and_start_course import find_and_start_course

    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [{username}] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger(username)
    log.info(f"▶ 帳號 {username} 開始執行")

    driver = open_browser(headless=headless)
    try:
        if not login(driver, username=username, password=password):
            log.error("登入失敗，結束此帳號")
            return

        if not find_and_start_course(driver):
            log.error("課程流程異常結束")
            return

        log.info("🎉 所有課程已完成")

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
    """格式：每行一筆 帳號:密碼，# 開頭為註解"""
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
# 主程式
# ══════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="E等公務園 多帳號同時學習")
    parser.add_argument("--headless", action="store_true", help="不顯示瀏覽器視窗")
    parser.add_argument("--accounts", type=str, default="",
                        help="帳號檔路徑（accounts.txt），留空使用程式內 ACCOUNTS 清單")
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

    workers = min(len(accounts), MAX_CONCURRENT)
    print(f"🚀 偵測到 {len(accounts)} 組帳號，同時啟動 {workers} 個")
    print(f"   headless={args.headless}，每組間隔 {STAGGER_SECONDS} 秒")
    print("=" * 60)

    active_procs = []
    for i, acc in enumerate(accounts[:workers]):
        p = multiprocessing.Process(
            target=run_single_account,
            args=(acc["username"], acc["password"], args.headless),
            name=f"Worker-{acc['username']}",
        )
        p.start()
        active_procs.append(p)
        print(f"[{i+1}/{workers}] 啟動帳號：{acc['username']} (PID {p.pid})")

        if i < workers - 1:
            time.sleep(STAGGER_SECONDS)

    print("\n⏳ 等待所有帳號完成...")
    for p in active_procs:
        p.join()

    print("\n✅ 所有帳號執行完畢")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()