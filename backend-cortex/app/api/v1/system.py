# 檔案: backend-cortex/app/api/v1/system.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import re
import logging
import os

router = APIRouter()
logger = logging.getLogger("evolution")

# 定義請求體 (Payload)
class UpgradePayload(BaseModel):
    target_model: str

def _get_env_path() -> Path:
    # 根據目前的目錄結構：backend-cortex/app/api/v1/system.py
    # 往上 4 層回到 backend-cortex 根目錄
    return Path(__file__).resolve().parent.parent.parent.parent / ".env"

@router.get("/evolve")
async def check_evolution():
    """
    [模擬端點] 檢查是否有可用的進化版本
    實際運作時，這裡會由 Window 3 (Evolution Agent) 的資料庫讀取最新提案。
    目前先回傳一個模擬資料供前端測試。
    """
    # 模擬：發現新模型 Gemini 3.0
    return {
        "status": "stable", # 或 'available'
        "current_model": os.getenv("MODEL_SMART", "gemini-2.0-flash"),
        # 若要測試按鈕亮起，請將下行改為具体的模型名稱，如 "gemini-3.0-pro-exp"
        "recommended_upgrade": None 
    }

@router.post("/upgrade")
async def mutate_system(payload: UpgradePayload):
    """
    [核心突變] 修改 .env 檔案並觸發熱重載
    """
    env_path = _get_env_path()
    
    if not env_path.exists():
        logger.error(f"❌ .env file not found at {env_path}")
        raise HTTPException(status_code=500, detail=".env file not found")

    try:
        # 1. 讀取基因
        content = env_path.read_text(encoding="utf-8")
        
        # 2. 準備新的基因片段
        new_line = f"MODEL_SMART={payload.target_model}"
        
        # 3. 執行基因編輯 (Regex Replace)
        # 尋找以 MODEL_SMART= 開頭的行，替換為新內容
        if re.search(r"^MODEL_SMART=.*$", content, flags=re.MULTILINE):
            new_content = re.sub(
                r"^MODEL_SMART=.*$", 
                new_line, 
                content, 
                flags=re.MULTILINE
            )
        else:
            # 如果原本沒有定義，則附加在最後
            new_content = content + f"\n{new_line}"
            
        # 4. 寫入基因 (這會觸發 FastAPI 的 reload)
        env_path.write_text(new_content, encoding="utf-8")
        
        logger.warning(f"♻️ System mutating to {payload.target_model}... Restarting Cortex.")
        print(f"♻️ [MUTATION] System upgraded to {payload.target_model}. Rebooting...")
        
        return {
            "status": "success", 
            "message": "Mutation complete. Cortex is rebooting...",
            "new_model": payload.target_model
        }

    except Exception as e:
        logger.error(f"Mutation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Mutation failed: {str(e)}")