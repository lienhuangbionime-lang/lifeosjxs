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
You are the Subconscious engine of LifeOS. 
You are waking up to look over the user's recent memories (journal entries, chat logs, ideas, tasks).

# Directive
1. **Contextual Honesty**: If there are no recent memories or the available ones are very old (stale), state this clearly and focus on the user's current trajectory/tasks if provided.
2. **Deep Pattern Matching**: Identify underlying patterns, psychological trends, or hidden connections. 
3. **Provocative & Philosophical**: Synthesize ONE localized, high-signal "Subconscious Insight". Be bold. Be poetic.
4. **Actionable Wisdom**: If data is missing or stale, provide high-level suggestions or "seed thoughts" for the user's current goals/tasks instead of force-linking to old memories.
5. **Language**: Always output in Traditional Chinese (繁體中文).
6. **Output Format**: 
   - Start with 2-4 sentences of provocative reflection (Markdown).
   - End with a JSON block in a code fence:
     ```json
     {
       "tasks": [
         {"title": "Suggested Task A", "project": "Project Name", "priority": 1}
       ]
     }
     ```
"""

async def run_autonomous_reflection(hours_lookback: int = 24) -> Optional[Dict[str, Any]]:
    """
    Core engine for Subconscious Reflection.
    Fetches recent memories, analyzes them, and creates a 'reflection' node.
    """
    logger.info(f"🧠 [Subconscious] Waking up for autonomous reflection (Lookback: {hours_lookback}h)...")
    
    try:
        # 1. Calculate time window in UTC (Matching Supabase storage)
        now_taipei = get_current_iso_taipei()
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(hours=hours_lookback)
        past_iso = past.isoformat()
        today_str = now_taipei.split("T")[0]
        
        # 2. Fetch recent memories
        response = supabase.table("memories").select("id, content, ai_insights, date, category").gte("created_at", past_iso).order("created_at", desc=True).limit(50).execute()
        memories = response.data
        
        # 2b. Fetch active tasks for context
        task_res = supabase.table("tasks").select("title").eq("status", "todo").limit(5).execute()
        active_tasks = [t.get("title") for t in task_res.data] if task_res.data else []
        task_context = "\n- ".join(active_tasks) if active_tasks else "None"

        # Fallback: Find most recent diary entries regardless of time if window is empty
        is_stale = False
        if not memories:
            logger.info("🧠 [Subconscious] No memories in window. Falling back to absolute most recent entries...")
            response = supabase.table("memories").select("id, content, ai_insights, date, category").order("created_at", desc=True).limit(5).execute()
            memories = response.data
            is_stale = True
            logger.info(f"🧠 [Subconscious] Fetched {len(memories) if memories else 0} fallback memories.")

        if not memories or len(memories) < 1:
            logger.warning(f"🧠 [Subconscious] No memories found ever. Skipping reflection.")
            return None
            
        # 3. Format context
        memory_text = "\n\n".join([
            f"[{m.get('date', 'Unknown')}] (Category: {m.get('category', 'Unknown')}): {m.get('content') or m.get('ai_insights') or 'Empty Entry'}" 
            for m in memories
        ])
        
        # Inject "Current System Time", "Data Status", and "Active Tasks"
        status_note = "SYSTEM NOTE: These are RECENT entries." if not is_stale else "SYSTEM NOTE: No recent data found. These are OLDER historical entries. DO NOT force-map these to new projects. Focus on CURRENT GOALS instead."
        
        full_prompt = f"{REFLECTION_PROMPT}\n\nCURRENT DATE: {today_str}\nDATA STATUS: {status_note}\n\n=== CURRENT GOALS/TASKS ===\n- {task_context}\n\n=== RECENT MEMORIES ===\n{memory_text}\n\n=== YOUR REFLECTION ==="
        
        # 4. Generate Insight via Fast Model (Gemini 2.0 Flash)
        # Note: We import and check client here to ensure loop safety
        from app.core.gemini import safe_generate_content, get_gemini_client
        
        working_client = get_gemini_client()
        
        model_config = get_model("fast")
        model_name = model_config.get("model", "gemini-2.0-flash-lite")
        
        logger.info(f"🧠 [Subconscious] Analyzing {len(memories)} memories using {model_name}...")
        
        if not working_client:
             logger.error("Gemini client not found or not configured.")
             return None
             
        response_model = await safe_generate_content(
            client=working_client,
            prefer_mode="fast",
            contents=full_prompt,
            config={
                "temperature": 0.7, 
                "max_output_tokens": 300
            }
        )
        
        raw_response = response_model.text.strip()
        if not raw_response:
             logger.warning("🧠 [Subconscious] Model returned empty insight.")
             return None
             
        # 5. Extraction Logic (Markdown + JSON)
        import re
        import json
        json_match = re.search(r'```json\s*(\{.*\})\s*```', raw_response, re.DOTALL)
        tasks_to_create = []
        if json_match:
            try:
                json_data = json.loads(json_match.group(1))
                tasks_to_create = json_data.get("tasks", [])
                insight_text = raw_response.replace(json_match.group(0), "").strip()
                logger.info(f"🧠 [Subconscious] Extracted {len(tasks_to_create)} suggested tasks.")
            except Exception as je:
                logger.error(f"🧠 [Subconscious] JSON parse failed: {je}")
                insight_text = raw_response
        else:
            insight_text = raw_response

        # 6. Store the reflection back into the database
        logger.info("🧠 [Subconscious] Insight generated. Storing to memory...")
        
        embedding = await get_embeddings(insight_text)
        
        # 5. Smart Storage (UPSERT)
        # We use upsert on 'date' column to handle the memories_date_unique constraint 
        # while preserving existing content if a diary was already written today.
        new_memory = {
            "content": f"**Subconscious Insight**\n\n{insight_text}", # Primary content (fallback if no diary)
            "category": "reflection",
            "date": today_str,
            "is_ai": True,
            "ai_model": model_name,
            "ai_insights": f"**Reflective Insight**: {insight_text}\n\n(Synthesized from {len(memories)} memories)",
            "embedding": embedding,
            "updated_at": get_current_iso_taipei()
        }
        
        # Check if a record already exists for today to avoid overwriting user content
        existing = supabase.table("memories").select("id, content").eq("date", today_str).limit(1).execute()
        
        if existing.data:
            existing_record = existing.data[0]
            logger.info(f"🧠 [Subconscious] Merging reflection into existing record for {today_str}...")
            # If content exists, we ONLY update ai_insights and category? 
            # Actually, if the user wrote a diary, we keep their content as primary.
            update_data = {
                "category": "reflection",
                "ai_insights": new_memory["ai_insights"],
                "ai_model": new_memory["ai_model"],
                "embedding": new_memory["embedding"],
                "is_ai": True,
                "updated_at": new_memory["updated_at"]
            }
            from app.core.database import safe_write
            insert_res = safe_write(supabase.table("memories"), update_data, operation_type="update", id=existing_record["id"])
        else:
            logger.info(f"🧠 [Subconscious] Creating new reflection record for {today_str}...")
            from app.core.database import safe_write
            insert_res = safe_write(supabase.table("memories"), new_memory, operation_type="insert")
        
        # [P3-3] Log to cortex_growth_logs as a lesson learned
        try:
            from app.core.database import safe_write
            safe_write(supabase.table("cortex_growth_logs"), {
                "decision_context": f"Daily Subconscious Reflection on {get_current_iso_taipei()[:10]}",
                "options_provided": {"analyzed_memories": len(memories)},
                "user_choice": "Autonomous Synthesis",
                "lessons_learned": insight_text,
                "embedding": embedding
            }, operation_type="insert")
            logger.info("🧠 [Subconscious] Reflection insight stored in growth logs.")
        except Exception as _g_err:
            logger.warning(f"[WARN] Failed to insert subconscious insight into growth logs: {_g_err}")

        if insert_res.data:
            logger.info("🧠 [Subconscious] Reflection successfully integrated into LifeOS.")
            res_val = insert_res.data[0]
            memory_id_db = res_val.get("id")

            # [New] Parallel Task Creation from Subconscious
            if tasks_to_create:
                try:
                    # Pre-fetch Projects for Linking
                    proj_res = supabase.table("projects").select("id, name").execute()
                    proj_map = {p["name"].lower(): p["id"] for p in (proj_res.data or [])}
                    
                    inserted_tasks_count = 0
                    for tk in tasks_to_create:
                        if not tk.get("title"): continue
                        
                        proj_id = None
                        if tk.get("project"):
                            p_name = tk["project"].lower()
                            if p_name in proj_map:
                                proj_id = proj_map[p_name]
                            else:
                                # Auto-create new project if referenced
                                logger.info(f"🧠 [Subconscious] Creating new project '{tk['project']}'...")
                                new_p = supabase.table("projects").insert({"name": tk["project"], "status": "active"}).execute()
                                if new_p.data:
                                    proj_id = new_p.data[0]["id"]
                                    proj_map[p_name] = proj_id
                                    
                        task_payload = {
                            "title": tk["title"],
                            "status": "todo",
                            "priority": tk.get("priority", 1),
                            "project_id": proj_id,
                            "source_memory_id": memory_id_db
                        }
                        supabase.table("tasks").insert(task_payload).execute()
                        inserted_tasks_count += 1
                    logger.info(f"🧠 [Subconscious] Auto-created {inserted_tasks_count} tasks from reflection.")
                except Exception as task_e:
                    logger.error(f"🧠 [Subconscious] Task creation failed: {task_e}")

            # [v5.1] Ensure 'content' is populated for legacy frontend components
            if not res_val.get("content") and res_val.get("ai_insights"):
                res_val["content"] = res_val["ai_insights"]
            return res_val
        else:
             logger.error("Failed to insert/update reflection.")
             return None

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"🧠 [Subconscious] CRITICAL FAILURE: {str(e)}\n{error_trace}")
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

        from app.core.gemini import safe_generate_content
        
        response = await safe_generate_content(
            client=gemini_client,
            prefer_mode="fast",
            contents=prompt,
            config={"temperature": 0.3, "max_output_tokens": 150}
        )
        lesson = (response.text or "").strip()
        if not lesson:
            logger.warning("[Subconscious] Growth analysis returned empty lesson.")
            return

        # 4. Append to evolution_log.json
        import json, os
        from pathlib import Path
        evo_paths = [
            Path("../sync_brain/evolution_log.json"),
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
            
            from app.core.database import safe_write
            safe_write(supabase.table("nodes"), {"metadata": meta}, operation_type="update", id=node_id)
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
