import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Routers
from app.api.v1 import ingest as ingest_router_mod
from app.api.v1 import memories as memories_router_mod
from app.api.v1 import system as system_router_mod
from app.api.v1 import analyze as analyze_router_mod
from app.api.v1.endpoints import projects as projects_router_mod

app.include_router(analyze_router_mod.router, prefix="/api/v1/analyze", tags=["Analyze"])
app.include_router(chat_router_mod.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(projects_router_mod.router, prefix="/api/v1/projects", tags=["Projects"])


# 根路徑檢查
@app.get("/")
def root():
    return {
        "status": "online",
        "system": "LifeOS v3.1 Autopoiesis",
        "cortex": "Active"
    }

@app.on_event("startup")
async def on_startup():
    logger.info("🧠 Cortex is waking up...")
    try:
        subconscious_scheduler.start_scheduler()
    except Exception as e:
        logger.error(f"Scheduler error: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("💤 Cortex is sleeping...")
    try:
        subconscious_scheduler.stop_scheduler()
    except Exception as e:
        logger.error(f"Scheduler shutdown error: {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, log_level="info")