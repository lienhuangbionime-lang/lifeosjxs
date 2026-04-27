# app/subconscious/scheduler.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
from app.services.subconscious import run_autonomous_reflection

from apscheduler.triggers.cron import CronTrigger
from skills.evolution.monthly_consolidator import MonthlyConsolidator

logger = logging.getLogger("app.subconscious.scheduler")

scheduler: AsyncIOScheduler = AsyncIOScheduler()

async def scheduled_monthly_consolidation():
    """Trigger the Monthly Consolidator skill."""
    try:
        logger.info("?? [Scheduler] Commencing Monthly Strategic Consolidation...")
        consolidator = MonthlyConsolidator()
        await consolidator.run_consolidation()
    except Exception as e:
        logger.error(f"Monthly consolidation failed: {e}")

async def scheduled_reflection():
    """Wrapper to run reflection in the background."""
    try:
        logger.info("?? [Scheduler] Triggering scheduled autonomous reflection...")
        await run_autonomous_reflection(hours_lookback=48)
    except Exception as e:
        logger.error(f"Scheduled reflection failed: {e}")


def start_scheduler():
    try:
        # add job if not added
        # run every 10 minutes
        scheduler.add_job(heartbeat, trigger=IntervalTrigger(minutes=10), id="heartbeat", replace_existing=True)
        # Background Autonomous Reflection: Default run every 12 hours
        scheduler.add_job(scheduled_reflection, trigger=IntervalTrigger(hours=12), id="autonomous_reflection", replace_existing=True)
        
        # [NEW] Monthly Strategic Consolidation: Run on the 1st of every month at midnight
        scheduler.add_job(scheduled_monthly_consolidation, trigger=CronTrigger(day=1, hour=0, minute=0), id="monthly_consolidation", replace_existing=True)

        scheduler.start()
        logger.info("Scheduler started: Heartbeat (10m), Reflection (12h), Monthly Consolidation (1st/month).")
    except Exception as e:
        logger.exception("Failed to start scheduler: %s", e)


def stop_scheduler():
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler shut down")
    except Exception as e:
        logger.exception("Failed to stop scheduler: %s", e)
