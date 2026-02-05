import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Routers
from app.api.v1 import ingest as ingest_router_mod
from app.api.v1 import memories as memories_router_mod
from app.api.v1 import system as system_router_mod

from app.subconscious import scheduler as subconscious_scheduler

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend-cortex")

app = FastAPI(
    title="LifeOS Cortex",
    version="3.1.0",
    docs_url="/docs",
    openapi_url="/api/v1/openapi.json"
)

# [Fix] 加入 CORS 設定，防止前端被擋
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生產環境建議改為前端 Vercel 域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Router 掛載修正 ---

# 1. Ingest (感知)
# 修正邏輯：因為 ingest.py 裡面已經寫了 @router.post("/ingest")
# 所以這裡 prefix 只要寫 "/api/v1" 即可。
# 最終路徑: /api/v1/ingest
app.include_router(ingest_router_mod.router, prefix="/api/v1", tags=["Ingest"])

# 2. Memories (記憶)
# 修正邏輯：memories.py 裡面寫的是 @router.get("/daily")
# 這裡 prefix 寫 "/api/v1/memories"
# 最終路徑: /api/v1/memories/daily
app.include_router(memories_router_mod.router, prefix="/api/v1/memories", tags=["Memories"])

# 3. System (進化)
# 修正邏輯：system.py 裡面寫的是 @router.get("/evolve")
# 這裡 prefix 寫 "/api/v1/system"
# 最終路徑: /api/v1/system/evolve
app.include_router(system_router_mod.router, prefix="/api/v1/system", tags=["System"])


# [Fix] 根路徑處理 (解決 "Not Found" 錯誤)
@app.get("/")
def root():
    return {
        "status": "online",
        "system": "LifeOS v3.1 Autopoiesis",
        "cortex": "Active",
        "docs_url": "/docs"
    }

@app.on_event("startup")
async def on_startup():
    logger.info("🧠 Cortex is waking up: starting scheduler...")
    try:
        subconscious_scheduler.start_scheduler()
    except Exception as e:
        logger.error(f"Failed to start subconscious scheduler: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("💤 Cortex is sleeping: stopping scheduler...")
    try:
        subconscious_scheduler.stop_scheduler()
    except Exception as e:
        logger.error(f"Failed to stop subconscious scheduler: {e}")

if __name__ == "__main__":
    # 確保 Render/Railway 的 PORT 環境變數能被讀取
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"🚀 Server starting on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, log_level="info")