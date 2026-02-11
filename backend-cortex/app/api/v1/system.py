# app/api/v1/system.py
from fastapi import APIRouter, HTTPException
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from app.core.gemini import get_model
from app.models.schemas import (
    SystemStatusResponse, 
    UpgradeResponse, 
    PromptRequest, 
    PromptResponse
)


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
        # Get real usage from DB
        try:
            from app.core.usage import get_daily_usage
            usage = await get_daily_usage()
            count = usage.get("request_count", 0)
            
            # Gemini Free Limit: 1500 RPD for Flash/Lite, 50 for Pro
            is_pro = "pro" in current_model.lower()
            limit = 50 if is_pro else 1500
            remaining = max(0, limit - count)
            
            model_label = "Pro" if is_pro else "Flash/Lite"
            remaining_info = f"{remaining} / {limit} ({model_label} Quota Today)"
        except Exception as e:
            remaining_info = "Free Tier (Usage tracking active)"

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
    """
    try:
        logger.info("Evolution triggered via /api/v1/system/upgrade")
        return UpgradeResponse(success=True, message="Evolution triggered (simulated).")
    except Exception as e:
        logger.exception("Upgrade trigger failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to trigger upgrade")


@router.get("/prompts/{name}", response_model=PromptResponse)
async def get_prompt(name: str):
    """
    Retrieve a system prompt by name.
    """
    import os
    from pathlib import Path
    
    prompt_dir = Path(__file__).parent.parent.parent.parent / "prompts"
    file_path = prompt_dir / f"{name}.md"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
    
    try:
        content = file_path.read_text(encoding="utf-8")
        mtime = os.path.getmtime(file_path)
        last_modified = datetime.fromtimestamp(mtime).isoformat()
        
        return PromptResponse(name=name, content=content, last_modified=last_modified)
    except Exception as e:
        logger.error(f"Error reading prompt {name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read prompt")


from app.models.schemas import PromptRequest
@router.post("/prompts/{name}", response_model=PromptResponse)
async def update_prompt(name: str, request: PromptRequest):
    """
    Update a system prompt.
    """
    import os
    from pathlib import Path
    
    prompt_dir = Path(__file__).parent.parent.parent.parent / "prompts"
    file_path = prompt_dir / f"{name}.md"
    
    # Check if directory exists, if not create it (safety)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        file_path.write_text(request.content, encoding="utf-8")
        mtime = os.path.getmtime(file_path)
        last_modified = datetime.fromtimestamp(mtime).isoformat()
        
        logger.info(f"Prompt '{name}' updated via API.")
        return PromptResponse(name=name, content=request.content, last_modified=last_modified)
    except Exception as e:
        logger.error(f"Error updating prompt {name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update prompt")
