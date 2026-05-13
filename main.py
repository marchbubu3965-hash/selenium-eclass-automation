"""
main.py
統一入口：依序呼叫 5 支子腳本，完成完整的自動學習流程。

執行方式：
    python main.py
    python main.py --course "資訊安全" --max-hours 4
    python main.py --headless
"""

import sys
import os
import time
import threading
import argparse
import logging

# 確保不論從哪裡執行，都能找到同資料夾的模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from open_browser              import open_browser
from login                     import login
from find_and_start_course     import find_and_start_course
from anti_idle                 import run_anti_idle_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="E等公務園自動化學習")
    parser.add_argument("-u", "--username",  default=config.USERNAME,  help="登入帳號")
    parser.add_argument("-p", "--password",  default=config.PASSWORD,  help="登入密碼")
    parser.add_argument("-t", "--max-hours", type=float, default=config.MAX_HOURS, help="最長學習時數")
    parser.add_argument("--headless",        action="store_true",      help="不顯示瀏覽器視窗")
    return parser.parse_args()


def main():
    args = parse_args()

    log.info("=" * 50)
    log.info("  E等公務園 自動化學習腳本啟動")
    log.info("=" * 50)

    # ── STEP 1：開啟瀏覽器 ─────────────────
    log.info("\n📌 STEP 1 / 5：開啟瀏覽器")
    driver = open_browser(headless=args.headless)

    try:
        # ── STEP 2：登入 ──────────────────────
        log.info("\n📌 STEP 2 / 5：登入")
        if not login(driver, username=args.username, password=args.password):
            log.error("登入失敗，程式終止")
            return

        # ── STEP 3：找課程並開始上課 ──────────
        log.info("\n📌 STEP 3 / 5：找課程並開始上課")
        if not find_and_start_course(driver): 
            log.error("無法進入課程，程式終止")
            return

        # ── STEP 4 & 5：防閒置 + 偵測完成（並行）─
        log.info("\n📌 STEP 4 / 5：啟動防閒置")
        log.info("📌 STEP 5 / 5：啟動課程完成偵測")

        stop_flag = [False]   # 共用停止旗標
        max_secs  = args.max_hours * 3600

        # 防閒置執行緒
        idle_thread = threading.Thread(
            target=run_anti_idle_loop,
            args=(driver, config.ANTI_IDLE_INTERVAL, stop_flag),
            daemon=True,
            name="AntiIdle",
        )

        idle_thread.start()
        log.info(f"⏳ 學習中... 最長執行 {args.max_hours} 小時（Ctrl+C 可手動中止）")

        # 主執行緒等待：完成 or 超時
        start_time = time.time()
        while not stop_flag[0]:
            elapsed = time.time() - start_time
            if elapsed >= max_secs:
                log.warning(f"⏰ 已達最大學習時間 {args.max_hours} 小時，結束程式")
                stop_flag[0] = True
            time.sleep(5)

        # 等執行緒結束
        idle_thread.join(timeout=5)

    except KeyboardInterrupt:
        log.info("\n⚠️  使用者手動中止")

    finally:
        log.info("\n🔚 關閉瀏覽器")
        driver.quit()
        log.info("✅ 程式結束")


if __name__ == "__main__":
    main()