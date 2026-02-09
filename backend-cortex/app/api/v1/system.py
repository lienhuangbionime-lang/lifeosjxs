# app/api/v1/system.py
from fastapi import APIRouter, HTTPException
import logging
from typing import Dict

from app.core.gemini import get_model
from app.models.schemas import SystemStatusResponse, UpgradeResponse

router = APIRouter()
logger = logging.getLogger("app.api.v1.system")


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Return system status including current model and available versions.
    """
    try:
        import google.generativeai as genai
        
        fast = get_model("fast")
        smart = get_model("smart")
        # choose current model based on env preference or default to fast
        current_choice = "smart" if smart.get("configured") else "fast"
        current_model = smart["model"] if current_choice == "smart" else fast["model"]

        status = "ok" if (fast.get("configured") or smart.get("configured")) else "degraded"
        
        # Try to fetch real quota information from Gemini API
        remaining_info = "Unknown"
        try:
            if smart.get("configured"):
                # Get model info to check quota
                model_info = genai.get_model(f"models/{current_model}")
                
                # Check if quota info is available
                if hasattr(model_info, 'rate_limit'):
                    rate_limit = model_info.rate_limit
                    # Format: "requests_per_minute / requests_per_day"
                    rpm = getattr(rate_limit, 'requests_per_minute', 'N/A')
                    rpd = getattr(rate_limit, 'requests_per_day', 'N/A')
                    remaining_info = f"RPM: {rpm}, RPD: {rpd}"
                else:
                    # Fallback for free tier
                    remaining_info = "Free Tier (1500 RPD)"
        except Exception as quota_err:
            logger.warning(f"Could not fetch quota info: {quota_err}")
            remaining_info = "Free Tier (Check Console)"

        return SystemStatusResponse(
            status=status,
            current_model=current_model,
            model_versions=[fast["model"], smart["model"]],
            remaining_requests=remaining_info,
            note="Models obtained from app/core/gemini factory."
        )
    except Exception as e:
        logger.exception("Failed to get system status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")


@router.post("/upgrade", response_model=UpgradeResponse)
async def trigger_upgrade():
    """
    Simulate an upgrade/evolution trigger.
    Note: we MUST NOT write to .env in cloud environments. This endpoint logs the action and returns success.
    TODO: In the future, record an upgrade request to the supabase `system_config` table and let a deployment job act on it.
    """
    try:
        # Simulated action
        logger.info("Evolution triggered via /api/v1/system/upgrade")
        # TODO: optionally write to supabase system_config table (deferred)
        return UpgradeResponse(success=True, message="Evolution triggered (simulated).")
    except Exception as e:
        logger.exception("Upgrade trigger failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to trigger upgrade")