# main.py
import os
import logging

from fastapi import FastAPI
import uvicorn

# routers
from app.api.v1 import ingest as ingest_router_mod
from app.api.v1 import memories as memories_router_mod
from app.api.v1 import system as system_router_mod

from app.subconscious import scheduler as subconscious_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend-cortex")

app = FastAPI(title="backend-cortex (LifeOS)")

# include routers with prefixes as requested
app.include_router(ingest_router_mod.router, prefix="/api/v1/ingest", tags=["ingest"])
app.include_router(memories_router_mod.router, prefix="/api/v1/memories", tags=["memories"])
app.include_router(system_router_mod.router, prefix="/api/v1/system", tags=["system"])


@app.on_event("startup")
async def on_startup():
    logger.info("Application startup: starting scheduler")
    try:
        subconscious_scheduler.start_scheduler()
    except Exception:
        logger.exception("Failed to start subconscious scheduler on startup")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown: stopping scheduler")
    try:
        subconscious_scheduler.stop_scheduler()
    except Exception:
        logger.exception("Failed to stop subconscious scheduler on shutdown")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, log_level="info")