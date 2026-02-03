# backend-cortex/app/subconscious/scheduler.py
"""
Subconscious Scheduler: 背景排程維護任務，不阻塞 API。
"""
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler


_scheduler: Optional[BackgroundScheduler] = None


def start_scheduler() -> None:
    """建立並啟動 BackgroundScheduler，加入 evolution 掃描作業。"""
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler()

    # 每天執行一次進化檢查
    _scheduler.add_job(
        "app.subconscious.evolution:check_for_upgrades",
        trigger="interval",
        hours=24,
        id="evolution_scan",
        replace_existing=True,
    )

    _scheduler.start()
    print("[Scheduler] Background scheduler started (evolution_scan every 24h).")
