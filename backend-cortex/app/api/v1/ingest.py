# app/api/v1/ingest.py
from fastapi import APIRouter, HTTPException
from typing import Any
import logging
import asyncio
from datetime import datetime

from app.models.schemas import LogEntrySchema
from app.core.database import supabase
from app.core.gemini import get_model  # ensure import path uses app.core

router = APIRouter()
logger = logging.getLogger("app.api.v1.ingest")


@router.post("/", response_model=LogEntrySchema)
async def ingest_log(entry: LogEntrySchema):
    """
    Ingest a new LogEntry into the 'LogEntry' table in supabase.
    - Uses app.core.gemini only if needed (import path corrected).
    - Defensive behavior if supabase is not configured.
    """
    if supabase is None:
        logger.warning("Supabase client unavailable; cannot ingest log.")
        raise HTTPException(status_code=503, detail="Database unavailable (supabase not configured).")

    try:
        payload = entry.dict(exclude_unset=True)
        # Ensure date is an ISO string for DB if necessary
        if isinstance(payload.get("date"), datetime):
            payload["date"] = payload["date"].isoformat()

        def insert():
            return supabase.table("LogEntry").insert(payload).execute()

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, insert)

        data = getattr(result, "data", None) or result.get("data") if isinstance(result, dict) else None
        error = getattr(result, "error", None) or result.get("error") if isinstance(result, dict) else None

        if error:
            logger.error("Supabase error while inserting log: %s", error)
            raise HTTPException(status_code=500, detail="Database insert error")

        # return the first inserted row if available
        created = (data[0] if isinstance(data, list) and len(data) > 0 else payload)
        return created
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to ingest log entry: %s", e)
        raise HTTPException(status_code=500, detail="Unexpected error ingesting log")