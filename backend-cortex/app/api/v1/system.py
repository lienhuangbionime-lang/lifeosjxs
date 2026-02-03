# 檔案位置: backend-cortex/app/api/v1/system.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv

# 引入潛意識進化邏輯 (如果還沒建立 evolution.py，這行可能會報錯，我們先做簡單版)
# from app.subconscious.evolution import check_for_upgrades 

router = APIRouter()
logger = logging.getLogger("uvicorn")

class UpgradeRequest(BaseModel):
    target_model: str

@router.get("/evolve")
async def check_evolution():
    """
    [模擬] 檢查是否有新模型可用的端點
    """
    try:
        # 暫時回傳模擬數據，確保 API 不會崩潰
        return {
            "current_model": os.getenv("MODEL_SMART", "gemini-2.0-flash"),
            "recommended_upgrade": None, # 暫時不建議升級
            "message": "Evolution Agent is strictly monitoring."
        }
    except Exception as e:
        logger.error(f"Evolution Check Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upgrade")
async def execute_upgrade(request: UpgradeRequest):
    """
    [危險] 修改 .env 檔案並觸發重啟
    """
    try:
        env_path = ".env"
        if not os.path.exists(env_path):
            raise FileNotFoundError(".env file not found")

        # 讀取現有內容
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 替換模型變數
        new_lines = []
        found = False
        for line in lines:
            if line.startswith("MODEL_SMART="):
                new_lines.append(f"MODEL_SMART={request.target_model}\n")
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f"\nMODEL_SMART={request.target_model}\n")

        # 寫回檔案
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        logger.warning(f"🧬 System Mutated: Switched to {request.target_model}")
        return {"status": "success", "message": "System mutation complete. Restarting..."}

    except Exception as e:
        logger.error(f"Mutation Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))