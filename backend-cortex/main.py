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

# [Fix 1] 確保 CORS 允許前端連線
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 為了方便除錯先全開，正式環境可改為 Vercel 網址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- [Fix 2] 路由掛載修正 (關鍵修正點) ---

# Ingest: 
# ingest.py 裡面是 @router.post("/ingest")
# 這裡 prefix 設為 "/api/v1"
# 組合結果: /api/v1/ingest (正確!)
app.include_router(ingest_router_mod.router, prefix="/api/v1", tags=["Ingest"])

# Memories:
# memories.py 裡面是 @router.get("/") (注意：這裡通常設為根)
# 這裡 prefix 設為 "/api/v1/memories"
# 組合結果: /api/v1/memories/ (正確!)
app.include_router(memories_router_mod.router, prefix="/api/v1/memories", tags=["Memories"])

# System:
# system.py 裡面是 @router.get("/status") 或 similar
# 這裡 prefix 設為 "/api/v1/system"
# 組合結果: /api/v1/system/status (正確!)
app.include_router(system_router_mod.router, prefix="/api/v1/system", tags=["System"])


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