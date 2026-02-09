# app/core/scheduler.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Import service logic
# from app.api.v1.analyze import analyze_monthly (moved inside function)
# from app.api.v1.ingest import process_daily_digest (example)

logger = logging.getLogger("cortex.scheduler")

class SubconsciousScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start_scheduler(self):
        if self.is_running:
            return

        # Example Task: Monthly Analysis at 1st of month
        # self.scheduler.add_job(
        #     self.run_monthly_analysis,
        #     trigger=CronTrigger(day=1, hour=2, minute=0),
        #     id="monthly_analysis",
        #     replace_existing=True
        # )

        self.scheduler.start()
        self.is_running = True
        logger.info("Subconscious Scheduler started.")

    def stop_scheduler(self):
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Subconscious Scheduler stopped.")

    async def run_monthly_analysis(self):
        logger.info("Running scheduled monthly analysis...")
        from app.api.v1.analyze import analyze_monthly
        # await analyze_monthly(...)
        pass

subconscious_scheduler = SubconsciousScheduler()
