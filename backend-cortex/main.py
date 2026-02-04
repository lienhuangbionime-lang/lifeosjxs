# 檔案: backend-cortex/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.subconscious.scheduler import start_scheduler
from app.api.v1 import system, ingest, memories  # 確保這三個檔案都存在
import uvicorn
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cortex")

app = FastAPI(
    title="LifeOS Cortex",
    version="3.1.0",
    description="Biological Operating System Backend",
    openapi_url="/api/v1/openapi.json"
)

# 允許跨域 (讓 Vercel 前端能連線)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生產環境建議改為前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 掛載神經分區 (Routers) ---
# 1. 系統進化 (Evolution)
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
# 2. 感知輸入 (Ingest) - 將原本寫死在 main 的邏輯移到這裡
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingest"])
# 3. 記憶檢索 (Memories)
app.include_router(memories.router, prefix="/api/v1/memories", tags=["Memories"])

@app.on_event("startup")
def on_startup() -> None:
    """應用啟動時喚醒潛意識 (Scheduler)"""
    logger.info("🧠 Cortex is waking up...")
    start_scheduler()

@app.get("/")
def root():
    return {"status": "online", "message": "LifeOS v3.1 Cortex is active."}

if __name__ == "__main__":
    # 使用 Port 8001 避免與其它服務衝突
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
