# app/api/v1/memories.py
from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional
from datetime import datetime
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
        from app.core.database import get_supabase_client
        db = get_supabase_client()
        res = db.table("memories").insert(entry).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Failed to create memory: {e}")
        raise e

# --- Endpoints ---

@router.post("", response_model=dict)
async def add_memory(entry: LogEntrySchema, request: Request):
    """
    Manual memory insertion endpoint.
    """
    from app.core.database import get_request_client
    db = get_request_client(request)
    if getattr(db, "_is_guest_mode", False):
        raise HTTPException(status_code=403, detail="Guest Mode cannot alter memories.")

    data = await create_memory_entry(
        content=entry.content,
        date=entry.date,
        tags=entry.tags or [],
        source="manual_api"
    )
    return {"success": True, "data": data}

@router.get("", response_model=List[LogEntrySchema])
async def get_recent_memories(
    request: Request,
    limit: int = 20,
    q: Optional[str] = Query(None, description="Search query (semantic or keyword)")
):
    """
    Retrieve memories.
    - If `q` is provided: Performs Semantic Search (Vector).
    - If `q` is None: Returns recent memories (Chronological).
    """
    from app.core.database import get_request_client
    db = get_request_client(request)

    if db is None:
        logger.warning("Supabase client unavailable; cannot fetch memories.")
        raise HTTPException(status_code=503, detail="Database unavailable (supabase not configured).")

    is_guest = getattr(db, "_is_guest_mode", False)

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
                sql_query = db.table("memories").select("*")
                
                # [Phase F] Guest Mode Constraint Lock
                if is_guest:
                    sql_query = sql_query.or_("is_private.eq.false,is_private.is.null")
                    
                result = sql_query.order("date", desc=True).limit(limit).execute()
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
        logger.warning("Memories fetch failed (likely connection issue): %s", e)
        return []


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
async def trigger_monthly_review(year: int, month: int, request: Request, force: bool = True):
    """
    [v5.4] Trigger Monthly Review generation — always upserts (force regenerate by default).
    Runs inline in FastAPI as a background task. No subprocess required.
    Uses dynamic model selection from registry (zero hardcoded model IDs).
    """
    import asyncio
    import calendar as cal
    from app.core.database import get_request_client
    from app.core.gemini import get_request_gemini_client, safe_generate_content, types

    db = get_request_client(request)
    g_client = get_request_gemini_client(request)

    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")
    if not g_client:
        raise HTTPException(status_code=503, detail="Gemini client unavailable — check API key")

    async def _run_generation():
        try:
            # 1. Fetch ALL memories for the month (including newly added ones)
            start_date = f"{year}-{month:02d}-01"
            _, last_day = cal.monthrange(year, month)
            end_date = f"{year}-{month:02d}-{last_day}"

            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: db.table("memories")
                    .select("date,content,ai_insights,mood,energy,focus")
                    .gte("date", start_date)
                    .lte("date", end_date)
                    .order("date")
                    .execute()
            )
            memories = resp.data or []
            if not memories:
                logger.warning(f"No memories for {year}-{month:02d}, skipping review generation.")
                return

            # 2. Build daily summary text
            month_name = cal.month_name[month]
            daily_lines = []
            for m in memories:
                content = m.get("ai_insights") or m.get("content") or ""
                preview = content[:500] + "..." if len(content) > 500 else content
                mood = m.get("mood", "N/A")
                energy = m.get("energy", "N/A")
                daily_lines.append(f"### {m.get('date', '?')} (Mood: {mood}, Energy: {energy})\n{preview}")
            context_text = "\n\n".join(daily_lines)

            # 3. Construct AI prompt
            prompt = f"""You are the Cortex Monthly Review Agent.
Below are the daily summaries for {month_name} {year}.

Synthesize these into a high-level Monthly Review in Traditional Chinese.
Structure your response in Markdown:

# Monthly Review: {month_name} {year}

## 🏆 Key Achievements
- ...

## 🧗 Challenges & Roadblocks
- ...

## 💡 Insights & Lessons Learned
- ...

## 🔋 Energy & Mood Trends
- ...

## 🎯 Focus for Next Month
- ...

---
Daily Summaries ({len(memories)} entries):
{context_text}
"""

            # 4. Generate with dynamic model (from registry, not hardcoded)
            response = await safe_generate_content(
                client=g_client,
                prefer_mode="smart",  # Use smart model for monthly synthesis; falls back to fast
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.5)
            )

            if not response or not response.text:
                logger.error(f"Monthly review generation returned empty for {year}-{month:02d}")
                return

            review_text = response.text.strip()

            # 5. Upsert (overwrites existing review — this is the key for re-generation)
            payload = {
                "year": year,
                "month": month,
                "summary": review_text,
            }
            # [v5.4 FIX] Use delete + insert instead of upsert.
            await loop.run_in_executor(
                None,
                lambda: db.table("MonthlyReview")
                    .delete()
                    .eq("year", year)
                    .eq("month", month)
                    .execute()
            )
            from app.core.database import safe_insert
            await loop.run_in_executor(
                None,
                lambda: safe_insert(db.table("MonthlyReview"), payload)
            )
            logger.info(f"Monthly Review for {year}-{month:02d} saved ({len(memories)} memories, {len(review_text)} chars)")


        except Exception as e:
            logger.exception(f"Monthly review generation failed for {year}-{month:02d}: {e}")

    # Fire off the background task and return immediately so the frontend can start polling
    asyncio.create_task(_run_generation())
    return {
        "status": "started",
        "message": f"Regenerating review for {year}-{month:02d} from {0} memories (force={force}). Poll /review/{year}/{month} every 5s.",
        "year": year,
        "month": month,
    }
