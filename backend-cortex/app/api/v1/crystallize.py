
from fastapi import APIRouter, HTTPException, BackgroundTasks
# We might need to create the worker later, but for now we sync the API
try:
    from app.workers.crystallize import crystallize_memories
except ImportError:
    def crystallize_memories(days):
        print(f"[MOCK] Crystallizing memories for {days} days")

import logging
import datetime
import json
from typing import Optional
from pydantic import BaseModel
from app.core.database import supabase
from app.core.gemini import get_model, gemini_client
from google.genai import types

router = APIRouter()
logger = logging.getLogger("cortex.api.crystallize")

# ---------------------------------------------------------------------------
# [Phase B] Pydantic Models
# ---------------------------------------------------------------------------
class DecisionLog(BaseModel):
    context: str                  # What was the decision about
    options: dict                 # {"A": "...", "B": "..."}
    user_choice: str              # "A" or "B"
    ai_prediction: str            # What AI predicted the user would choose
    lessons: Optional[str] = None # One-sentence lesson learned


@router.post("/crystallize")
async def trigger_crystallization(background_tasks: BackgroundTasks, days: int = 3):
    """
    Manually trigger the Crystallization Pipeline.
    Extracts Nodes & Edges from the last N days of memories.
    """
    logger.info(f"Received request to crystallize last {days} days.")
    
    # Run in background to avoid timeout
    background_tasks.add_task(crystallize_memories, days)
    
    return {"status": "accepted", "message": "Crystallization started in background."}

@router.get("/contextual-prompts")
async def get_contextual_prompts():
    """
    Agentic Phase 14: Context-Aware Capture.
    Reads recent memories and the latest Subconscious Reflection to generate 
    3 dynamic questions that bridge the gap between AI insights and user actions.
    """
    try:
        # 1. Fetch recent memories (last 48h) for temporal context
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(hours=48)
        
        # Use 'category' instead of 'type' (Schema Alignment)
        mem_res = supabase.table("memories").select("content, category, date, ai_insights") \
            .gte("created_at", past.isoformat()).order("created_at", desc=True).limit(15).execute()
        memories = mem_res.data or []
        
        # 2. Fetch the absolute latest Subconscious Reflection (The "Insight")
        ref_res = supabase.table("memories").select("content, ai_insights, date") \
            .eq("category", "reflection").order("created_at", desc=True).limit(1).execute()
        latest_ref = ref_res.data[0] if ref_res.data else None
        
        if not memories and not latest_ref:
            return {"prompts": ["今天過得好嗎？", "有什麼值得記錄的嗎？", "寫下你現在的想法吧！"]}
            
        # 3. Prepare Context
        context_parts = []
        if latest_ref:
            ref_text = latest_ref.get('content') or latest_ref.get('ai_insights')
            context_parts.append(f"=== LATEST AI INSIGHT ({latest_ref.get('date')}) ===\n{ref_text}")
            
        if memories:
            mem_text = "\n".join([f"[{m.get('date')}][{m.get('category')}] {m.get('content') or m.get('ai_insights')}" for m in memories])
            context_parts.append(f"=== RECENT ACTIVITY ===\n{mem_text}")
            
        full_context = "\n\n".join(context_parts)
        
        sys_prompt = '''You are the LifeOS context engine. Review the user's recent memories and the latest AI Subconscious Insight.
Generate exactly 3 short, thought-provoking questions (in Traditional Chinese) to guide their daily journal.
CRITICAL: If an "AI INSIGHT" is provided, at least 2 questions MUST follow up on the goals, patterns, or suggestions mentioned in that insight (e.g., if the insight mentions "Health focus", ask about their workout).
Keep questions concise and supportive.
Output JSON: {"prompts": ["Q1", "Q2", "Q3"]}'''

        # 4. Call fast model (Gemini 2.0 Flash) with improved resiliency
        from app.core.gemini import safe_generate_content
        try:
            ai_res = await safe_generate_content(
                client=gemini_client,
                prefer_mode="fast",
                contents=full_context,
                config=types.GenerateContentConfig(
                    system_instruction=sys_prompt,
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            
            result_json = json.loads(ai_res.text.strip())
            prompts = result_json.get("prompts", [])
        except Exception as ai_err:
            logger.warning(f"AI prompt generation failed (likely 429): {ai_err}")
            prompts = []
            
        # 5. Final Fallback Logic: If AI failed, use recent activity titles or static defaults
        if not prompts:
            if latest_ref:
                prompts = ["還記得早前的深度洞察嗎？點擊回顧...", "關於你的成長模式，有什麼新發現？"]
            elif memories:
                # Use a specific recent memory topic if possible
                latest_m = memories[0].get('content', '')[:20]
                prompts = [f"關於『{latest_m}...』還有什麼想補充的？", "今天的進度如何？", "有什麼值得紀錄的嗎？"]
            else:
                prompts = ["今天過得好嗎？", "有什麼值得記錄的嗎？", "準備好開始新的一天了嗎？"]
        
        return {"prompts": [p.replace("✨", "").strip() for p in prompts[:3]]}
        
    except Exception as e:
        logger.error(f"Failed to generate contextual prompts (outer): {e}")
        return {"prompts": ["今天過得好嗎？", "有什麼值得記錄的嗎？"]}


# ---------------------------------------------------------------------------
# [Phase B] Growth Log Endpoints — AI Self-Reflection
# ---------------------------------------------------------------------------

@router.post("/growth/log-decision")
async def log_decision(payload: DecisionLog):
    """
    Called by AI after every Glass Box Decision Matrix.
    Writes decision context, prediction vs actual choice, lessons, and embedding to cortex_growth_logs.
    Embedding enables semantic search across AI decision history.
    """
    try:
        prediction_match = payload.user_choice.strip().upper() == payload.ai_prediction.strip().upper()
        lesson_text = payload.lessons or (
            "Prediction matched." if prediction_match
            else f"Mismatch: AI predicted {payload.ai_prediction}, user chose {payload.user_choice}."
        )

        # Generate embedding from context + lesson (makes it semantically searchable)
        embed_text = f"{payload.context}\n{lesson_text}"
        embedding = None
        try:
            from app.services.embedder import generate_embedding
            embedding = await generate_embedding(embed_text)
        except Exception as _ee:
            logger.warning(f"[WARN] Embedding generation skipped: {_ee}")

        data = {
            "decision_context": payload.context,
            "options_provided": payload.options,
            "user_choice": payload.user_choice,
            "ai_prediction": payload.ai_prediction,
            "prediction_match": prediction_match,
            "lessons_learned": lesson_text,
        }
        if embedding:
            data["embedding"] = embedding

        supabase.table("cortex_growth_logs").insert(data).execute()
        logger.info(f"[OK] Decision logged. Match={prediction_match}, Embedding={'yes' if embedding else 'no'}")
        return {"status": "logged", "prediction_match": prediction_match}
    except Exception as e:
        logger.error(f"[ERROR] log_decision failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/growth/lessons")
async def get_lessons(limit: int = 10):
    """
    Returns recent AI lessons_learned from cortex_growth_logs.
    Used to prime the AI with its own past decision patterns.
    """
    try:
        res = (
            supabase.table("cortex_growth_logs")
            .select("decision_context, user_choice, ai_prediction, prediction_match, lessons_learned, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        lessons = res.data or []
        mismatch_rate = round(
            sum(1 for l in lessons if l.get("prediction_match") is False) / max(len(lessons), 1) * 100, 1
        )
        return {
            "lessons": lessons,
            "total": len(lessons),
            "mismatch_rate_pct": mismatch_rate
        }
    except Exception as e:
        logger.error(f"[ERROR] get_lessons failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/growth/search")
async def search_growth_logs(q: str, limit: int = 5):
    """
    Semantic search over AI decision history using match_growth_logs RPC.
    Used by AI to recall similar past decisions before making new ones.
    """
    try:
        from app.services.embedder import generate_embedding
        query_embedding = await generate_embedding(q)
        if not query_embedding:
            raise HTTPException(status_code=400, detail="Embedding generation failed")

        res = supabase.rpc("match_growth_logs", {
            "query_embedding": query_embedding,
            "match_threshold": 0.5,
            "match_count": limit
        }).execute()

        return {
            "query": q,
            "results": res.data or [],
            "total": len(res.data or [])
        }
    except Exception as e:
        logger.error(f"[ERROR] search_growth_logs failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


