# app/subconscious/scheduler.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio

logger = logging.getLogger("app.subconscious.scheduler")

scheduler: AsyncIOScheduler = AsyncIOScheduler()


def heartbeat():
    logger.info("heartbeat: system is alive")


def start_scheduler():
    try:
        # add job if not added
        # run every 10 minutes
        scheduler.add_job(heartbeat, trigger=IntervalTrigger(minutes=10), id="heartbeat", replace_existing=True)
        scheduler.start()
        logger.info("Scheduler started with heartbeat every 10 minutes")
    except Exception as e:
        logger.exception("Failed to start scheduler: %s", e)


def stop_scheduler():
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler shut down")
    except Exception as e:
        logger.exception("Failed to stop scheduler: %s", e)