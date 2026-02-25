# app/core/scheduler.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("cortex.scheduler")

class SubconsciousScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start_scheduler(self):
        if self.is_running:
            return

        # [Phase B+] Autonomous Reflection — every 12 hours
        self.scheduler.add_job(
            self._run_reflection,
            trigger=IntervalTrigger(hours=12),
            id="autonomous_reflection",
            replace_existing=True,
            misfire_grace_time=300
        )

        # [Phase B] Growth Log Analysis — every 12 hours (offset 30 min)
        self.scheduler.add_job(
            self._run_growth_analysis,
            trigger=IntervalTrigger(hours=12, jitter=1800),
            id="growth_analysis",
            replace_existing=True,
            misfire_grace_time=300
        )

        # [Phase E] Knowledge Decay (Brain Cleanup) — every 12 hours (offset 60 min)
        self.scheduler.add_job(
            self._run_knowledge_decay,
            trigger=IntervalTrigger(hours=12, jitter=3600),
            id="knowledge_decay",
            replace_existing=True,
            misfire_grace_time=300
        )

        self.scheduler.start()
        self.is_running = True
        logger.info("[OK] Subconscious Scheduler started (reflection + growth analysis, 12h interval).")

    def stop_scheduler(self):
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("[OK] Subconscious Scheduler stopped.")

    async def _run_reflection(self):
        try:
            from app.services.subconscious import run_autonomous_reflection
            await run_autonomous_reflection(hours_lookback=24)
        except Exception as e:
            logger.error(f"[ERROR] Scheduled reflection failed: {e}")

    async def _run_growth_analysis(self):
        try:
            from app.services.subconscious import run_growth_analysis
            await run_growth_analysis()
        except Exception as e:
            logger.error(f"[ERROR] Scheduled growth analysis failed: {e}")

    async def _run_knowledge_decay(self):
        try:
            from app.services.subconscious import run_knowledge_decay
            await run_knowledge_decay()
        except Exception as e:
            logger.error(f"[ERROR] Scheduled knowledge decay failed: {e}")

subconscious_scheduler = SubconsciousScheduler()
