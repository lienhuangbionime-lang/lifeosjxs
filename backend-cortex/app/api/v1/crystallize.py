
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
from app.core.database import supabase
from app.core.gemini import get_model, gemini_client
from google.genai import types

router = APIRouter()
logger = logging.getLogger("cortex.api.crystallize")

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
    Reads recent memories and generates 3 dynamic questions to guide the user's daily journal.
    """
    try:
        # 1. Fetch recent memories covering the last 48 hours for context
        now = datetime.datetime.now()
        past = now - datetime.timedelta(hours=48)
        
        response = supabase.table("memories").select("content, type, date").gte("created_at", past.isoformat()).order("created_at", desc=True).limit(20).execute()
        memories = response.data
        
        if not memories:
            return {"prompts": ["今天過得好嗎？", "有什麼值得記錄的嗎？", "寫下你現在的想法吧！"]}
            
        # 2. Prepare Context for Gemini Flash
        context_text = "\n".join([f"[{m.get('date')}][{m.get('type')}] {m.get('content')}" for m in memories])
        
        sys_prompt = '''You are the LifeOS context engine. Review the user's recent memories and chat logs.
Generate exactly 3 short, thought-provoking questions (in Traditional Chinese) to guide their daily journal today.
Do not ask generic questions. Base them SPECIFICALLY on what they were doing or talking about recently.
For example, if they worked on "Supabase", ask "Supabase 資料表今天有什麼新進展嗎？"
Output JSON: {"prompts": ["Q1", "Q2", "Q3"]}'''

        # 3. Call fast model
        model_name = "gemini-2.5-flash"
        
        if not gemini_client:
             return {"prompts": ["今天過得好嗎？", "有什麼值得記錄的嗎？", "最近忙碌嗎？"]}
             
        ai_res = gemini_client.models.generate_content(
            model=model_name,
            contents=context_text,
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                response_mime_type="application/json",
                temperature=0.7
            )
        )
        
        result_json = json.loads(ai_res.text.strip())
        prompts = result_json.get("prompts", ["今天有什麼特別的發現嗎？"])
        
        return {"prompts": prompts[:3]}
        
    except Exception as e:
        logger.error(f"Failed to generate contextual prompts: {e}")
        return {"prompts": ["今天過得好嗎？", "有什麼值得記錄的嗎？"]}
