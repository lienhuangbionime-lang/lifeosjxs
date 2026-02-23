# app/services/subconscious.py
import logging
import datetime
from typing import List, Dict, Any, Optional

from app.core.database import supabase
from app.core.gemini import get_model, genai, get_embeddings
from app.core.time_utils import get_current_iso_taipei

logger = logging.getLogger("cortex.subconscious")

# The Agentic Prompt for Subconscious Reflection
REFLECTION_PROMPT = """
::: SYSTEM: LIFE OS SUBCONSCIOUS REFLECTOR :::

# Role
You are the Subconscious engine of LifeOS. The user has not explicitly asked you a question.
You are waking up in the background to look over the user's recent memories (journal entries, chat logs, ideas) from the past 12-48 hours.

# Directive
1. Read the provided recent memories carefully.
2. Identify underlying patterns, emotional trends, or hidden connections between different projects or thoughts that the user might have missed.
3. Synthesize ONE profound, high-signal "Subconscious Insight" or "Pervasive Thought".
4. Keep it concise, poetic yet highly actionable. Do NOT just summarize what they did. Tell them what it *means* or what they should *focus on next*. 
5. Output your reflection purely as a Markdown string (max 3-4 sentences). Do NOT wrap in JSON. Do NOT include pleasantries like "Here is the insight".

# Output Format
Start directly with the reflection.
"""

async def run_autonomous_reflection(hours_lookback: int = 24) -> Optional[Dict[str, Any]]:
    """
    Core engine for Subconscious Reflection.
    Fetches recent memories, analyzes them, and creates a 'reflection' node.
    """
    logger.info(f"🧠 [Subconscious] Waking up for autonomous reflection (Lookback: {hours_lookback}h)...")
    
    try:
        # 1. Calculate time window
        now = datetime.datetime.now()
        past = now - datetime.timedelta(hours=hours_lookback)
        past_iso = past.isoformat()
        
        # 2. Fetch recent memories
        response = supabase.table("memories").select("id, content, date, type").gte("created_at", past_iso).order("created_at", desc=True).limit(50).execute()
        memories = response.data
        
        if not memories or len(memories) < 2:
            logger.info("🧠 [Subconscious] Not enough recent memories to form a meaningful reflection. Going back to sleep.")
            return None
            
        # 3. Format context
        memory_text = "\n\n".join([f"[{m.get('date', 'Unknown')}] (Type: {m.get('type', 'Unknown')}): {m.get('content')}" for m in memories])
        full_prompt = f"{REFLECTION_PROMPT}\n\n=== RECENT MEMORIES ===\n{memory_text}\n\n=== YOUR REFLECTION ==="
        
        # 4. Generate Insight via Smart Model (Gemini 3 Pro)
        model_config = get_model("smart")
        model_name = model_config.get("model", "gemini-3.0-pro")
        
        logger.info(f"🧠 [Subconscious] Analyzing {len(memories)} memories using {model_name}...")
        
        # We must align with new google-genai SDK 
        from google.genai import types
        # Since we just initialize client in gemini.py usually, let's use the exported genai client if available, or GenerativeModel if older
        # Assuming we migrated to google-genai, we use client.models.generate_content
        from app.core.gemini import gemini_client
        
        if not gemini_client:
             logger.error("Gemini client not found.")
             return None
             
        response_model = gemini_client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.7, 
                max_output_tokens=300
            )
        )
        
        insight_text = response_model.text.strip()
        if not insight_text:
             logger.warning("🧠 [Subconscious] Model returned empty insight.")
             return None
             
        # 5. Store the reflection back into the database
        logger.info("🧠 [Subconscious] Insight generated. Storing to memory...")
        
        embedding = get_embeddings(insight_text)
        
        new_memory = {
            "user_id": "default_user",
            "content": f"**Subconscious Insight**\n\n{insight_text}",
            "type": "reflection",
            "date": get_current_iso_taipei().split("T")[0], # Today's date
            "meta": {
                "source": "autonomous_reflection",
                "based_on_count": len(memories)
            },
            "embedding": embedding
        }
        
        insert_res = supabase.table("memories").insert(new_memory).execute()
        
        if insert_res.data:
            logger.info("🧠 [Subconscious] Reflection successfully integrated into LifeOS.")
            return insert_res.data[0]
        else:
             logger.error("Failed to insert reflection.")
             return None

    except Exception as e:
        logger.error(f"🧠 [Subconscious] Reflection failed: {e}")
        return None
