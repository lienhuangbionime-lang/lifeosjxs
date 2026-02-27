# app/api/v1/memories.py
from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional
import logging
import asyncio
import os
import sys

from app.models.schemas import LogEntrySchema
from app.core.database import supabase
from app.core.vector import vector_engine

router = APIRouter()
logger = logging.getLogger("app.api.v1.memories")


# --- Internal Helpers ---
async def create_memory_entry(content: str, source: str = "system", tags: List[str] = [], date: Optional[str] = None):
    """
    Internal helper to create a memory entry.
    Used by: tasks.py (completion logs), ingest.py (daily logs), etc.
    """
    if not date:
        from app.core.time_utils import get_today_str_taipei
        date = get_today_str_taipei()
        
    entry = {
        "date": date,
        "content": content,
        "category": source, # Use 'source' as category
        "is_ai": True if source == "system" else False,
        "tags": tags
    }
    
    try:
        res = supabase.table("memories").insert(entry).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Failed to create memory: {e}")
        raise e

# --- Endpoints ---

@router.post("/", response_model=dict)
async def add_memory(entry: LogEntrySchema):
    """
    Manual memory insertion endpoint.
    """
    data = await create_memory_entry(
        content=entry.content,
        date=entry.date,
        tags=entry.tags or [],
        source="manual_api"
    )
    return {"success": True, "data": data}

@router.get("/", response_model=List[LogEntrySchema])
async def get_recent_memories(
    limit: int = 20,
    q: Optional[str] = Query(None, description="Search query (semantic or keyword)")
):
    """
    Retrieve memories.
    - If `q` is provided: Performs Semantic Search (Vector).
    - If `q` is None: Returns recent memories (Chronological).
    """
    if supabase is None:
        logger.warning("Supabase client unavailable; cannot fetch memories.")
        raise HTTPException(status_code=503, detail="Database unavailable (supabase not configured).")

    try:
        # Case 1: Semantic Search
        if q and len(q.strip()) > 0:
            # Run vector search in thread pool
            def vector_search():
                results = vector_engine.search_memories(supabase, q, limit=limit)
                
                # [Schema Alignment]
                # RPC returns {id, content, metadata(json), similarity}
                # Pydantic expects flat {id, content, date, tags, mood...}
                mapped_results = []
                for row in results:
                    meta = row.get("metadata", {}) or {}
                    # [v4.3 Mapping Fix]
                    row_content = row.get("content")
                    row_insights = row.get("ai_insights")
                    final_content = row_insights if (row_insights and not row_content) else (row_content or "")
                    
                    mapped_results.append({
                        "id": row.get("id"),
                        "content": final_content,
                        "ai_insights": row_insights,
                        "date": meta.get("date") or row.get("date"),
                        "tags": meta.get("tags", []) or row.get("tags", []),
                        "category": meta.get("category") or row.get("category"),
                        "mood": meta.get("mood", 5),
                        "focus": meta.get("focus", 5),
                        "energy": meta.get("energy", 5),
                        "is_ai": row.get("is_ai", False),
                        "ai_model": row.get("ai_model")
                    })
                return mapped_results
            
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, vector_search)
            return data

        # Case 2: Recent Memories (Chronological)
        # supabase client is sync; run in thread to avoid blocking event loop
        def query():
            try:
                result = supabase.table("memories").select("*").order("date", desc=True).limit(limit).execute()
                return result
            except Exception as e:
                # bubble up
                raise

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, query)

        # supabase-py returns a dict-like object or APIResponse object
        if hasattr(result, "data"):
            data = result.data
            # [v4.3 Mapping Fix] Apply to chronological list
            if data:
                for item in data:
                    if not item.get("content") and item.get("ai_insights"):
                        item["content"] = item["ai_insights"]
        elif isinstance(result, dict):
            data = result.get("data")
            if data:
                for item in data:
                    if not item.get("content") and item.get("ai_insights"):
                        item["content"] = item["ai_insights"]
        else:
            data = None

        return data or []

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error fetching memories: %s", e)
        raise HTTPException(status_code=500, detail="Unexpected error fetching memories")


# --- Monthly Review Endpoints ---

@router.get("/review/{year}/{month}")
async def get_monthly_review(year: int, month: int, request: Request):
    """
    Get the monthly review for a specific month.
    """
    from app.core.database import get_request_client
    db = get_request_client(request)
    
    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        # Table name is "MonthlyReview"
        res = db.table("MonthlyReview").select("*").eq("year", year).eq("month", month).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching monthly review: {e}")
        return None 

@router.post("/review/{year}/{month}/generate")
async def trigger_monthly_review(year: int, month: int):
    """
    Trigger background generation of monthly review.
    """
    try:
        import subprocess
        from pathlib import Path
        
        # [Robust Pathing] Find scripts relative to this file
        # memories.py is in backend-cortex/app/api/v1/
        # tools is in project-root/tools/
        base_dir = Path(__file__).parent.parent.parent.parent.parent
        script_path = base_dir / "tools" / "generate_monthly_review.py"
        
        if not script_path.exists():
            # Fallback for deployments where tools might be in the app root
            script_path = base_dir / "backend-cortex" / "tools" / "generate_monthly_review.py"
            if not script_path.exists():
                logger.error(f"Review script not found at {script_path}")
                raise HTTPException(status_code=500, detail="Review generation script not found")

        # Use Popen to run in background
        process = subprocess.Popen(
            [sys.executable, str(script_path), str(year), str(month)],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            cwd=str(base_dir) # Run from project root
        )
        
        return {"status": "started", "pid": process.pid, "message": "Generation started in background"}
    except Exception as e:
        logger.error(f"Failed to trigger review generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))