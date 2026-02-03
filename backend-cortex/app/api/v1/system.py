# backend-cortex/app/api/v1/system.py
"""
System API: 系統管理路由（進化掃描、升級變異等）。
"""
import re
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.subconscious.evolution import check_for_upgrades

router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


class UpgradePayload(BaseModel):
    target_model: str


def _get_env_path() -> Path:
    """專案根目錄 (backend-cortex) 下的 .env。"""
    return Path(__file__).resolve().parent.parent.parent.parent / ".env"


@router.get("/system/evolve")
async def system_evolve():
    """
    手動觸發一次進化掃描，回傳掃描結果 JSON。
    與排程執行的 check_for_upgrades 相同邏輯，僅供管理端查詢。
    """
    report = check_for_upgrades()
    return report


@router.post("/system/upgrade")
async def system_upgrade(payload: UpgradePayload):
    """
    執行模型升級：寫入 .env 的 MODEL_SMART，並提示重啟。
    """
    env_path = _get_env_path()
    if not env_path.exists():
        raise HTTPException(status_code=500, detail=".env not found")

    try:
        content = env_path.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot read .env: {e}")

    # 正則：替換 MODEL_SMART=... 為 MODEL_SMART={target_model}
    new_content = re.sub(
        r"^MODEL_SMART=.*$",
        f"MODEL_SMART={payload.target_model}",
        content,
        flags=re.MULTILINE,
    )
    if new_content == content and "MODEL_SMART" not in content:
        new_content = content.rstrip() + "\nMODEL_SMART=" + payload.target_model + "\n"

    try:
        env_path.write_text(new_content, encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot write .env: {e}")

    logger.info("♻️ System mutating... Restarting Cortex.")
    print("♻️ System mutating... Restarting Cortex.")

    return {
        "status": "success",
        "message": "Mutation complete. Rebooting...",
    }
