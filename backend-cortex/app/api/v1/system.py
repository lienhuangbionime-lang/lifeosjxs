# backend-cortex/app/api/v1/system.py
"""
System API: 系統管理路由（進化掃描、維護等）。
"""
from fastapi import APIRouter

from app.subconscious.evolution import check_for_upgrades

router = APIRouter(tags=["system"])


@router.get("/system/evolve")
async def system_evolve():
    """
    手動觸發一次進化掃描，回傳掃描結果 JSON。
    與排程執行的 check_for_upgrades 相同邏輯，僅供管理端查詢。
    """
    report = check_for_upgrades()
    return report
