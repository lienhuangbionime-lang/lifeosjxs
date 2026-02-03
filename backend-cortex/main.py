# backend-cortex/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.core.config import settings
from app.core.gemini import get_model
from app.subconscious.scheduler import start_scheduler
from app.api.v1.system import router as system_router
import uvicorn

app = FastAPI(
    title="LifeOS Cortex",
    openapi_url="/api/v1/openapi.json"
)

# 掛載 System API
app.include_router(system_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup() -> None:
    """應用啟動時啟動背景排程器。"""
    start_scheduler()

# --- 定義資料模型 (與前端對接) ---
class LogRequest(BaseModel):
    text: str
    date: str

# --- 定義路由 ---
@app.get("/")
def root():
    return {"message": "LifeOS v3.1 Cortex is running. Brain is active."}

@app.post("/api/v1/ingest")
async def ingest_log(request: LogRequest):
    """
    接收前端的日誌，並呼叫 Gemini 進行處理
    """
    print(f"📥 Cortex received: {request.text[:50]}...")
    
    try:
        # 1. 喚醒 AI 模型 (使用我們之前寫好的 Bypass 或 SDK Client)
        client = get_model("fast") # 使用快速模型
        
        # 2. 進行思考 (這裡暫時回傳簡單回應，確保連線成功)
        # 未來這裡會接上 Sorter Agent
        response = client.generate_content(f"請分析這段日誌並給出簡短回應: {request.text}")
        
        # 3. 回傳給前端 (格式必須符合 CaptureView 的預期)
        return {
            "success": True,
            "model": settings.MODEL_SMART,
            "data": {
                "markdown_body": response.text, # AI 的回應文字
                "meta": {
                    "metrics": {"mood": 5, "focus": 5, "energy": 5},
                    "date": request.date
                },
                "tasks": []
            }
        }
    except Exception as e:
        print(f"🔥 Cortex Error: {str(e)}")
        # 回傳錯誤給前端，讓 CaptureView 顯示
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)