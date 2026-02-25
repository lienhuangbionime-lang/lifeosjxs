# app/services/subconscious.py
import logging
import datetime
from typing import List, Dict, Any, Optional

from app.core.database import supabase
from app.core.gemini import get_model, genai, get_embeddings, types, gemini_client
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
        
        if not gemini_client:
             logger.error("Gemini client not found.")
             return None
             
        response_model = await gemini_client.aio.models.generate_content(
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
        
        embedding = await get_embeddings(insight_text)
        
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
        
        # [P3-3] Log to cortex_growth_logs as a lesson learned
        try:
            supabase.table("cortex_growth_logs").insert({
                "decision_context": f"Daily Subconscious Reflection on {get_current_iso_taipei()[:10]}",
                "options_provided": {"analyzed_memories": len(memories)},
                "user_choice": "Autonomous Synthesis",
                "lessons_learned": insight_text,
                "embedding": embedding
            }).execute()
            logger.info("🧠 [Subconscious] Reflection insight stored in growth logs.")
        except Exception as _g_err:
            logger.warning(f"[WARN] Failed to insert subconscious insight into growth logs: {_g_err}")

        if insert_res.data:
            logger.info("🧠 [Subconscious] Reflection successfully integrated into LifeOS.")
            return insert_res.data[0]
        else:
             logger.error("Failed to insert reflection.")
             return None

    except Exception as e:
        logger.error(f"[ERROR] [Subconscious] Reflection failed: {e}")
        return None


async def run_growth_analysis() -> None:
    """
    [Phase B] Reads recent cortex_growth_logs, identifies recurring mistake patterns,
    and appends a learning entry to evolution_log.json.
    Runs every 12h alongside run_autonomous_reflection().
    """
    logger.info("[Subconscious] Running growth log analysis...")
    try:
        # 1. Fetch recent growth logs (last 30)
        res = supabase.table("cortex_growth_logs") \
            .select("decision_context,user_choice,ai_prediction,prediction_match,lessons_learned,created_at") \
            .order("created_at", desc=True) \
            .limit(30) \
            .execute()

        logs = res.data or []
        if len(logs) < 3:
            logger.info("[Subconscious] Not enough growth log entries to analyze yet.")
            return

        # 2. Compute stats
        judged = [l for l in logs if l.get("prediction_match") is not None]
        mismatches = [l for l in judged if l.get("prediction_match") is False]
        accuracy = round(len(judged) - len(mismatches)) / max(len(judged), 1) * 100

        # 3. Ask Gemini to identify patterns in mistakes
        model_config = get_model("fast")
        model_name = model_config.get("model", "gemini-1.5-flash")

        lessons_text = "\n".join([
            f"- [{l.get('created_at','?')[:10]}] Mismatch: AI predicted '{l.get('ai_prediction')}', user chose '{l.get('user_choice')}'. Lesson: {l.get('lessons_learned','')}"
            for l in mismatches[:10]
        ]) or "No recent mismatches found."

        prompt = f"""You are a meta-cognitive AI analyzer reviewing your own past decision errors.

Recent AI Prediction Mismatches (last 30 sessions):
{lessons_text}

Overall prediction accuracy: {accuracy:.0f}%

Based on these patterns, write ONE brief "lesson learned" entry (2-3 sentences max) that:
1. Identifies the most common type of mistake
2. States a concrete behavioral adjustment to avoid it
3. Is written in first person ("I should...")

Output only the lesson text, no headers or preamble."""

        response = await gemini_client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=150)
        )
        lesson = (response.text or "").strip()
        if not lesson:
            logger.warning("[Subconscious] Growth analysis returned empty lesson.")
            return

        # 4. Append to evolution_log.json
        import json, os
        from pathlib import Path
        evo_paths = [
            Path("sync_brain/evolution_log.json"),
            Path(r"c:\Users\lien.huang\AppData\lifeosjxs\sync_brain\evolution_log.json"),
        ]
        evo_path = next((p for p in evo_paths if p.exists()), None)
        if evo_path:
            with open(evo_path, "r", encoding="utf-8") as f:
                evo_log = json.load(f)
            evo_log.append({
                "timestamp": get_current_iso_taipei(),
                "event": "growth_analysis",
                "type": "ai_lesson",
                "description": lesson,
                "meta": {
                    "source": "run_growth_analysis",
                    "prediction_accuracy_pct": round(accuracy, 1),
                    "judged_decisions": len(judged),
                    "mismatch_count": len(mismatches)
                }
            })
            with open(evo_path, "w", encoding="utf-8") as f:
                json.dump(evo_log, f, ensure_ascii=False, indent=2)
            logger.info(f"[OK] Growth lesson appended to evolution_log.json (accuracy={accuracy:.0f}%)")
        else:
            logger.warning("[WARN] evolution_log.json not found, lesson not persisted.")

    except Exception as e:
        logger.error(f"[ERROR] Growth analysis failed: {e}")

async def run_knowledge_decay() -> Dict[str, Any]:
    """
    [Phase E] Identifies 'cold' nodes (> 30 days without mention) and marks them as archived.
    Reduces noise in the Neural Graph and RAG context.
    """
    logger.info("[Subconscious] Running knowledge decay audit...")
    try:
        # 1. Calculate the 30-day threshold
        threshold_days = 30
        now = datetime.datetime.now()
        threshold_date = (now - datetime.timedelta(days=threshold_days)).date().isoformat()

        # 2. Get all active nodes (not already archived in metadata)
        # Note: We skip 'project' type nodes as they have their own lifecycle
        res_nodes = supabase.table("nodes").select("id, label, metadata") \
            .neq("type", "project") \
            .execute()
        
        all_nodes = res_nodes.data or []
        active_nodes = [n for n in all_nodes if not n.get("metadata", {}).get("archived")]

        if not active_nodes:
            logger.info("[Subconscious] No active nodes found for decay audit.")
            return {"archived_count": 0}

        # 3. Get labels mentioned in memories within the last 30 days
        res_memories = supabase.table("memories") \
            .select("tags") \
            .gte("date", threshold_date) \
            .execute()
        
        recent_tags = set()
        for m in (res_memories.data or []):
            if m.get("tags"):
                recent_tags.update(m["tags"])

        # 4. Identify cold nodes
        cold_node_ids = []
        for node in active_nodes:
            label = node["label"]
            # A node is cold if its label hasn't been used in recent tags
            if label not in recent_tags:
                cold_node_ids.append(node["id"])

        # 5. Archive cold nodes by updating metadata
        archived_count = 0
        for node_id in cold_node_ids:
            # We fetch existing metadata to preserve other fields
            node = next(n for n in active_nodes if n["id"] == node_id)
            meta = node.get("metadata") or {}
            meta["archived"] = True
            meta["archived_at"] = get_current_iso_taipei()
            
            supabase.table("nodes").update({"metadata": meta}).eq("id", node_id).execute()
            archived_count += 1

        if archived_count > 0:
            logger.info(f"[OK] Knowledge decay complete. Archived {archived_count} cold nodes.")
            # Record the decay event in evolution_log
            from pathlib import Path
            import json
            evo_path = Path("sync_brain/evolution_log.json")
            if evo_path.exists():
                with open(evo_path, "r", encoding="utf-8") as f:
                    evo_log = json.load(f)
                evo_log.append({
                    "timestamp": get_current_iso_taipei(),
                    "event": "knowledge_decay",
                    "type": "cleanup",
                    "description": f"Archived {archived_count} nodes that haven't been used in {threshold_days} days.",
                    "meta": {"archived_nodes_count": archived_count}
                })
                with open(evo_path, "w", encoding="utf-8") as f:
                    json.dump(evo_log, f, ensure_ascii=False, indent=2)
        else:
            logger.info("[Subconscious] No cold nodes identified in this cycle.")

        return {"archived_count": archived_count}

    except Exception as e:
        logger.error(f"[ERROR] Knowledge decay failed: {e}")
        return {"error": str(e)}
