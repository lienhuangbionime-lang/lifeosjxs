"""
growth.py — Phase B: Cortex Growth Logs API
Enables AI to write its own decision history and read past lessons.
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import json

from app.core.database import get_supabase_client
from app.core.gemini import get_request_gemini_client

router = APIRouter()
logger = logging.getLogger("cortex.growth")


class LogDecisionRequest(BaseModel):
    decision_context: str           # What problem was being solved
    options_provided: dict          # {"A": "...", "B": "..."}
    user_choice: str                # Which option was chosen
    ai_prediction: Optional[str] = None       # What AI guessed would be chosen
    prediction_match: Optional[bool] = None   # Did the AI guess correctly?
    lessons_learned: Optional[str] = None     # What the AI learned from this


@router.post("/log-decision")
async def log_decision(request: Request, payload: LogDecisionRequest):
    """
    [Glass Box Protocol] Record an AI decision + outcome into cortex_growth_logs.
    The AI should call this after every significant architectural decision.
    """
    db = get_supabase_client(request)
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected.")

    try:
        # 1. Build the record
        record = {
            "decision_context": payload.decision_context,
            "options_provided": payload.options_provided,
            "user_choice": payload.user_choice,
        }
        if payload.ai_prediction is not None:
            record["ai_prediction"] = payload.ai_prediction
        if payload.prediction_match is not None:
            record["prediction_match"] = payload.prediction_match
        if payload.lessons_learned is not None:
            record["lessons_learned"] = payload.lessons_learned

        # 2. Generate embedding for semantic search later
        try:
            from app.services.embedder import generate_embedding
            embed_text = f"{payload.decision_context}\n{payload.lessons_learned or ''}"
            embedding = await generate_embedding(embed_text)
            if embedding:
                record["embedding"] = embedding
        except Exception as emb_e:
            logger.warning(f"[WARN] Embedding failed for growth log: {emb_e}")

        # 3. Insert
        res = db.table("cortex_growth_logs").insert(record).execute()
        inserted_id = res.data[0]["id"] if res.data else None

        logger.info(f"[OK] Growth log recorded: {inserted_id} | match={payload.prediction_match}")
        return {
            "success": True,
            "id": inserted_id,
            "prediction_match": payload.prediction_match
        }

    except Exception as e:
        logger.error(f"[ERROR] Failed to log decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lessons")
async def get_lessons(request: Request, limit: int = 20):
    """
    Retrieve the most recent AI lessons + prediction accuracy.
    Used by build_system_prompt() and subconscious reflection.
    """
    db = get_supabase_client(request)
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected.")

    try:
        res = db.table("cortex_growth_logs") \
            .select("id,decision_context,user_choice,ai_prediction,prediction_match,lessons_learned,created_at") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()

        lessons = res.data or []

        # Compute accuracy rate
        judged = [r for r in lessons if r.get("prediction_match") is not None]
        correct = [r for r in judged if r.get("prediction_match") is True]
        accuracy = round(len(correct) / len(judged) * 100, 1) if judged else None

        return {
            "lessons": lessons,
            "total": len(lessons),
            "prediction_accuracy_pct": accuracy,
            "judged_decisions": len(judged)
        }

    except Exception as e:
        logger.error(f"[ERROR] Failed to fetch lessons: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/scoring")
async def analyze_scoring_mismatches(request: Request, limit: int = 50):
    """
    Analyzes historical scoring discrepancies to detect structural AI bias.
    Identifies if the AI consistently over-estimates or under-estimates scores.
    """
    db = get_supabase_client(request)
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected.")

    try:
        # Search for Focus scoring discrepancy events
        res = db.table("cortex_growth_logs") \
            .select("options_provided,ai_prediction,user_choice,prediction_match") \
            .ilike("decision_context", "%Focus scoring discrepancy%") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()

        logs = res.data or []
        if not logs:
            return {
                "success": True,
                "message": "No scoring discrepancies found to analyze.",
                "bias_score": 0.0,
                "direction": "neutral",
                "sample_size": 0
            }

        total_delta = 0.0
        overscore_count = 0
        underscore_count = 0

        for log in logs:
            try:
                # Based on ingest.py: 
                # ai_score = float(focus)
                # user_choice = str(engine_score)
                ai_val = float(log.get("ai_prediction", 0))
                engine_val = float(log.get("user_choice", 0))
                
                delta = ai_val - engine_val
                total_delta += delta
                
                if delta > 0:
                    overscore_count += 1
                elif delta < 0:
                    underscore_count += 1
            except (ValueError, TypeError):
                continue

        avg_bias = total_delta / len(logs) if logs else 0.0
        direction = "overscoring" if avg_bias > 0.5 else ("underscoring" if avg_bias < -0.5 else "neutral")

        # Recommendation logic
        recommendation = ""
        if direction == "overscoring":
            recommendation = "AI is too optimistic. Suggest reducing FOCUS_WEIGHTS for 'completed_milestone'."
        elif direction == "underscoring":
            recommendation = "AI is too pessimistic. Suggest increasing FOCUS_WEIGHTS for 'deep_work_session'."
        else:
            recommendation = "Scoring is balanced within acceptable margin."

        return {
            "success": True,
            "avg_bias": round(avg_bias, 2),
            "direction": direction,
            "sample_size": len(logs),
            "stats": {
                "overscore_events": overscore_count,
                "underscore_events": underscore_count
            },
            "recommendation": recommendation
        }

    except Exception as e:
        logger.error(f"[ERROR] Scoring analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
