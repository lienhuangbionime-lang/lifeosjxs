from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import json
import datetime

# 引入核心模組
from app.core.gemini import get_model, get_embeddings, gemini_client, get_request_gemini_client
from app.core.database import supabase, get_request_client
from app.core.time_utils import get_today_str_taipei, get_current_iso_taipei
from app.services.crystallizer import crystallizer

router = APIRouter()
logger = logging.getLogger("cortex.ingest")

import os

def get_system_daily_prompt() -> str:
    """Reads the daily system prompt from the external markdown file."""
    prompt_path = os.path.join(os.path.dirname(__file__), "../../../prompts/system_daily.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read system_daily.md: {e}")
        # Return a minimal fallback if file reading fails
        return "::: SYSTEM: LIFE OS AGENTIC INGEST :::\n[Fallback Prompt due to file read error]"

async def auto_link_tasks_projects(content: str, db, http_request: Request) -> dict:
    """自動比對日記內容，標記已完成的現有任務，並更新專案活躍狀態。"""
    try:
        # 1. Fetch active tasks and projects
        tasks_res = db.table("tasks").select("id,title,project_id").eq("status", "todo").execute()
        proj_res = db.table("projects").select("id,name").in_("status", ["active"]).execute()
        
        active_tasks = tasks_res.data or []
        active_projects = proj_res.data or []

        if not active_tasks and not active_projects:
            return {"completed_tasks": 0, "projects_linked": 0}

        # 2. Ask Gemini to match
        from app.core.gemini import get_request_gemini_client
        from pydantic import BaseModel as pydantic_BaseModel

        class AutoLinkResult(pydantic_BaseModel):
            completed_task_ids: List[str]
            mentioned_project_ids: List[str]

        gemini = get_request_gemini_client(http_request)
        
        prompt = f"""
分析使用者的日記內容，判斷他們「是否明確完成了」清單上的哪些任務，以及「提到了」哪些專案。

【當前待辦任務清單】（JSON 陣列，包含 id 和 title）:
{json.dumps(active_tasks, ensure_ascii=False)}

【當前活躍專案清單】（JSON 陣列，包含 id 和 name）:
{json.dumps(active_projects, ensure_ascii=False)}

【使用者今日日記】:
{content}

你的任務：
1. `completed_task_ids`: 從待辦清單中，找出使用者在日記中暗示他「已經完成」的任務 ID。
   ⚠️ 極度重要：必須是「明確表示已經完成、做完、結束」的任務。如果使用者只是提到「正在進行、推進中、明天繼續」，或者如果是 Checkbox 但沒有打勾（例如 `- [ ]`），絕對不要列入！如果是打勾的（如 `- [x]`, `-[v]`）才算完成。
2. `mentioned_project_ids`: 從專案清單中，找出使用者在日記中提到的專案 ID。

僅回傳匹配到的 ID 字串陣列。若無任何匹配，回傳空陣列 []。
"""
        model_name = "gemini-2.0-flash"
        from app.core.gemini import safe_generate_content
        try:
            resp = await safe_generate_content(
                client=gemini,
                prefer_mode="fast",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AutoLinkResult,
                    "temperature": 0.1
                }
            )
            result_str = resp.text
        except Exception as e:
            logger = logging.getLogger("cortex.api.ingest.autolink")
            logger.error(f"Auto-link failed: {e}")
            result_str = None
            
        if result_str:
            result = json.loads(result_str)
            completed_ids = result.get("completed_task_ids", [])
            mentioned_ids = result.get("mentioned_project_ids", [])
            
            # 3. Update DB
            logger = logging.getLogger("cortex.api.ingest.autolink")
            
            # 3.1 Mark tasks done
            from app.core.database import safe_write
            for t_id in completed_ids:
                safe_write(db.table("tasks"), {"status": "done"}, operation_type="update", id=t_id)
                logger.info(f"Task marked done via auto-link: {t_id}")
                
            # 3.2 Update projects updated_at (to bubble them up as "focused")
            from app.core.time_utils import get_current_iso_taipei
            linked_project_names = []
            
            for p_id in mentioned_ids:
                # Get the project name for the UI toast
                p_name = next((p["name"] for p in active_projects if p["id"] == p_id), "未知專案")
                if p_name != "未知專案":
                    linked_project_names.append(p_name)
                    
                safe_write(db.table("projects"), {"updated_at": get_current_iso_taipei()}, operation_type="update", id=p_id)
                logger.info(f"Project updated_at bumped via auto-link: {p_id} ({p_name})")
                
            return {
                "completed_tasks": len(completed_ids),
                "projects_linked": len(mentioned_ids),
                "project_names": linked_project_names
            }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        logging.getLogger("cortex").error(f"Auto-link failed: {e}")
        
    return {"completed_tasks": 0, "projects_linked": 0, "project_names": []}

# 定義請求格式
class IngestRequest(BaseModel):
    content: str
    date: Optional[str] = None  # YYYY-MM-DD
    source: Optional[str] = "web_terminal" # NEW: capture, chat, web_terminal, etc.
    habits: Optional[List[str]] = []
    skipAi: bool = False
    mode: str = "append"

@router.post("")
@router.post("/")
async def ingest_log(http_request: Request, request: IngestRequest, background_tasks: BackgroundTasks):
    # Determine target table based on source
    # NEW: web_terminal and chat are considered user diaries -> memories
    target_table = "memories"
    if request.source and request.source not in ["capture", "web_terminal", "chat"]:
        target_table = "documents"
    
    logger.info(f"📥 Received INGEST request. Source: {request.source} -> Target: {target_table}")

    # Default date if missing
    ingest_date = request.date or get_today_str_taipei()
    habits_list = request.habits or []

    # [FIX] Extract date from content FIRST using Python regex
    # Use (?<!\d) and (?!\d) instead of \b to avoid Unicode word boundary issues (e.g. "2/1日記")
    import re as _re_date
    
    # 1. Match YYYY-MM-DD
    _date_explicit = _re_date.search(r'(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)', request.content)
    # 2. Match YYYY年M月D日
    _date_zh_full = _re_date.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', request.content)
    # 3. Match M月D日 (assume current year)
    _date_zh_short = _re_date.search(r'(?<!\d)(\d{1,2})月(\d{1,2})日', request.content)
    # 4. Match M/D or MM/DD (assume current year)
    _date_short = _re_date.search(r'(?<!\d)(\d{1,2})/(\d{1,2})(?!\d)', request.content)

    if _date_explicit:
        ingest_date = _date_explicit.group(1)
        logger.info(f"[OK] Date extracted from content (YYYY-MM-DD): {ingest_date}")
    elif _date_zh_full:
        year = _date_zh_full.group(1)
        month = _date_zh_full.group(2).zfill(2)
        day = _date_zh_full.group(3).zfill(2)
        ingest_date = f"{year}-{month}-{day}"
        logger.info(f"[OK] Date extracted from content (YYYY年M月D日): {ingest_date}")
    elif _date_zh_short:
        year = get_today_str_taipei()[:4]
        month = _date_zh_short.group(1).zfill(2)
        day = _date_zh_short.group(2).zfill(2)
        ingest_date = f"{year}-{month}-{day}"
        logger.info(f"[OK] Date extracted from content (M月D日): {ingest_date}")
    elif _date_short:
        year = get_today_str_taipei()[:4]  # e.g. "2026"
        month = _date_short.group(1).zfill(2)
        day = _date_short.group(2).zfill(2)
        ingest_date = f"{year}-{month}-{day}"
        logger.info(f"[OK] Short date extracted (M/D): {ingest_date}")
    
    db = get_request_client(http_request)
    req_gemini = get_request_gemini_client(http_request)
    
    # [NEW Phase P17] Multimodal Interpretation (Images, PDFs) for CaptureView
    # Target: ![filename](data:mime/type;base64,...)
    import re as _re_vision
    import base64
    from app.core.gemini import multimodal_interpret
    
    # Updated regex to support multiple mime-types (image, application/pdf)
    multimodal_matches = _re_vision.findall(r'!\[(.*?)\]\((data:(image/.*?|application/pdf);base64,.*?)\)', request.content)
    if multimodal_matches:
        logger.info(f"🔮 Detected {len(multimodal_matches)} multimodal items in content. Processing interpretation...")
        modified_content = request.content
        for filename, data_url, mime_type in multimodal_matches:
            try:
                # Extract base64
                encoded = data_url.split(",", 1)[1]
                file_bytes = base64.b64decode(encoded)
                
                # Interpret
                interpretation = await multimodal_interpret(file_bytes, mime_type)
                
                # Replace the blob with interpretation + link
                type_label = "📸 Image" if "image" in mime_type else "📄 Document"
                replacement = f"\n> **[{type_label} Interpretation: {filename}]**\n> {interpretation}\n"
                modified_content = modified_content.replace(f"![{filename}]({data_url})", replacement)
                logger.info(f"[OK] Interpreted {filename} ({mime_type})")
            except Exception as ve:
                logger.error(f"Multimodal processing failed for {filename}: {ve}")
        
        request.content = modified_content
    
    # Debug info
    logger.info(f"📥 Received INGEST request. Mode: {request.mode}, skipAi: {request.skipAi}")
    
    try:
        # 1. 呼叫 Gemini with v7.1 Prompt — [SDK v1] google.genai (not google.generativeai)
        model_config = get_model("fast")  # FAST model for ingest speed
        ai_data: Dict[str, Any] = {}
        model_name = model_config.get("model")

        # Skip AI if requested
        if not request.skipAi and model_config.get("configured") and req_gemini:
            # 構建使用者輸入 (注入 Today 作為基準日期)
            if not model_config.get("configured") or not req_gemini:
                logger.warning("[WARN] Cortex AI not configured. Running in simple storage mode.")
                request.skipAi = True
             
        if not request.skipAi:
            # 1. Structure text for LLM
            # Explicitly instruct the model to use the target ingest_date and user's manual metrics
            # [v7.2 FIX] Separate system role from user content:
            # system_instruction = who you are (Ingest Engine) ← system_daily.md
            # contents          = what to process (user's log today) ← user log
            system_instruction = get_system_daily_prompt()
            user_context = (
                f"[INSTRUCTION]\n"
                f"1. DATE: Use {ingest_date} everywhere. Replace [YYYY-MM-DD] with {ingest_date} in header and Graph Seeds.\n"
                f"2. METRICS: If the log contains '> Daily Metrics' with Mood/Focus/Energy numbers, preserve those exact values in the JSON.\n"
                f"3. JSON REQUIRED: End your response with a ```json ... ``` block containing: mood, focus, energy, category, tags, projects, is_private, facts, custom_metrics, AND 'tasks'.\n"
                f"   - 'tasks': Array of action items to be added to the task board. Look for numbered steps, MITs, or future commitments across ALL sections (including 'Project Progress'). Each MUST have 'title' and optional 'project'/'priority'. If none, use [].\n\n"
            )
            user_prompt = (
                f"{user_context}"
                f"[USER LOG - {ingest_date}]:\n{request.content}\n\n"
                f"[HABITS LOGGED]:\n{', '.join(habits_list) if habits_list else 'None'}"
            )

            
            # 2. Call Gemini API via Safe Failover Protocol
            try:
                from app.core.gemini import safe_generate_content
                response = await safe_generate_content(
                    client=req_gemini,
                    prefer_mode="fast",
                    contents=user_prompt,
                    system_instruction=system_instruction
                )
                
                logger.info("[OK] Gemini raw generation returned.")
                response_text = response.text.strip()
                
                # [v7.2 Fix] Improved JSON extraction:
                # 1. Try fenced ```json ... ``` block first (most reliable)
                # 2. Fallback: find outermost {} — use GREEDY match to capture full object,
                #    not first small {} which was the old bug (non-greedy {.*?} matched first '{}')
                logger.info(f"raw AI len: {len(response_text)}")
                import re
                json_match = re.search(r'```json\s*(\{.*\})\s*```', response_text, re.DOTALL)
                
                if not json_match:
                    logger.info("Regex json_match failed, trying fallback brace search")
                    # Greedy fallback: find last '{' to '}' span covering full JSON block
                    first_brace = response_text.rfind('\n{')
                    if first_brace == -1:
                        first_brace = response_text.find('{')
                    last_brace = response_text.rfind('}')
                    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                        json_candidate = response_text[first_brace:last_brace+1].strip()
                        logger.info(f"Fallback found candidate length: {len(json_candidate)}")
                        # Validate it looks like our schema
                        if '"mood"' in json_candidate or '"tags"' in json_candidate:
                            import types as _types
                            json_match = _types.SimpleNamespace(group=lambda n: json_candidate)
                            logger.info("Fallback candidate accepted via SimpleNamespace")
                
                if json_match:
                    json_str = json_match.group(1)
                    logger.info(f"JSON string extracted, len: {len(json_str)}")
                    # The rest is markdown
                    # We remove the JSON block from the response to get the clean markdown
                    try:
                        markdown_part = response_text.replace(json_match.group(0), "").strip()
                    except AttributeError:
                        # SimpleNamespace fallback doesn't have group(0), just use group(1)
                        markdown_part = response_text.replace(json_match.group(1), "").strip()
                    logger.info(f"Markdown extracted, len: {len(markdown_part)}")
                    
                    # Also strip any trailing/leading md code fences if they were wrapping the whole thing
                    markdown_part = re.sub(r'^```markdown\s*', '', markdown_part)
                    markdown_part = re.sub(r'\s*```$', '', markdown_part)
                    
                    try:
                        logger.info("Attempting json.loads")
                        ai_data = json.loads(json_str)
                        logger.info("json.loads SUCCESS")
                        if not isinstance(ai_data, dict):
                            ai_data = {}
                        
                        # Inject the extracted markdown if the JSON didn't already have a better one
                        if markdown_part and not ai_data.get("markdown_body"):
                            ai_data["markdown_body"] = markdown_part
                            
                        logger.info("[OK] Gemini JSON parsing complete with extracted Markdown.")
                    except json.JSONDecodeError as je:
                        logger.error(f"[ERROR] Gemini JSON Decode Error: {je}. Raw snippet: {json_str[:100]}")
                        ai_data = {}
                else:
                    logger.warning("[WARN] No JSON block found in AI response. Using fallback.")
                    ai_data = {}
                    
            except Exception as e:
                import traceback
                logger.error(f"[ERROR] Gemini API Error in ingest: type={type(e).__name__}, msg={e}")
                logger.error(traceback.format_exc())
                ai_data = {}

        elif request.skipAi:
            logger.info("[OK] AI Generation skipped by user request.")
        else:
            logger.warning("[WARN] req_gemini not configured, using fallback.")


        if not ai_data:
            # Fallback to basic structure
            ai_data = {
                "markdown_body": f"# [{ingest_date}] 日記\n\n{request.content}", 
                "meta": {
                    "date": ingest_date,
                    "metrics": {"mood": 5, "focus": 5, "energy": 5}
                }, 
                "tasks": [],
                "tags": [],
                "graph_seeds": []
            }

        # --- 核心邏輯修正：日期與分數對齊 ---
        # 1. 優先使用 AI 辨識出的日期，這能解決補寫日誌（如 2/1）的問題
        if not isinstance(ai_data, dict):
            ai_data = {}

        # 1. Date: ALWAYS use the user-supplied ingest_date. Never trust AI.
        # (AI date detection was causing wrong dates by overriding the user's input)
        meta = ai_data.get("meta") or {}

        # 2. Metrics Extraction (Robust + Fallback)
        # Try meta.metrics first (old format), then fallback to root ai_data (new format)
        metrics = meta.get("metrics") or ai_data
        mood = metrics.get("mood", ai_data.get("mood", 5))
        focus = metrics.get("focus", ai_data.get("focus", 5))
        energy = metrics.get("energy", ai_data.get("energy", 5))
        
        # 2.5 Force Override with Manual User Input (Regex Fallback)
        import re
        mood_match = re.search(r'- Mood:\s*(\d+)', request.content, re.IGNORECASE)
        if mood_match:
            try: mood = int(mood_match.group(1))
            except: pass
            
        focus_match = re.search(r'- Focus:\s*(\d+)', request.content, re.IGNORECASE)
        if focus_match:
            try: focus = int(focus_match.group(1))
            except: pass
            
        energy_match = re.search(r'- Energy:\s*(\d+)', request.content, re.IGNORECASE)
        if energy_match:
            try: energy = int(energy_match.group(1))
            except: pass
        
        logger.info(f"📊 Final metrics → Date={ingest_date}, Mood={mood}, Focus={focus}, Energy={energy}")

        # 3. Post-process markdown_body to enforce correct date + scores in TEXT
        markdown_body_raw = ai_data.get("markdown_body", "")
        if markdown_body_raw:
            import re as _re
            # Fix date in header: replace any "# [YYYY-MM-DD]" or "# YYYY-MM-DD" pattern with the correct date
            markdown_body_raw = _re.sub(
                r'#\s*\[?\d{4}-\d{2}-\d{2}\]?',
                f'# [{ingest_date}]',
                markdown_body_raw
            )
            # Fix date in Graph Seeds: replace [[YYYY-MM-DD]] or YYYY-MM-DD with correct date
            markdown_body_raw = _re.sub(
                r'\[?\[?\d{4}-\d{2}-\d{2}\]?\]?',
                f'[[{ingest_date}]]',
                markdown_body_raw
            )
            # Fix Mood score in Daily Metrics block
            markdown_body_raw = _re.sub(
                r'(>\s*-\s*Mood:\s*)\d+',
                f'\\g<1>{mood}',
                markdown_body_raw
            )
            # Fix Focus score
            markdown_body_raw = _re.sub(
                r'(>\s*-\s*Focus:\s*)\d+',
                f'\\g<1>{focus}',
                markdown_body_raw
            )
            # Fix Energy score
            markdown_body_raw = _re.sub(
                r'(>\s*-\s*Energy:\s*)\d+',
                f'\\g<1>{energy}',
                markdown_body_raw
            )
            ai_data["markdown_body"] = markdown_body_raw

        # ---------------------------------------------------------------
        # [Phase D] Scoring Engine Validation — AI Bias Detection
        # Compare AI-assigned focus score against fact-based calculation.
        # If delta > 2.0, log as a discrepancy to cortex_growth_logs.
        # ---------------------------------------------------------------
        if not request.skipAi and ai_data:
            try:
                from app.services.scoring_engine import scoring_engine

                # Build proxy facts from AI output (graph_seeds + task count)
                proxy_facts = []
                tasks_ai = ai_data.get("tasks", [])
                graph_seeds = ai_data.get("graph_seeds", [])

                if len(tasks_ai) >= 2:
                    proxy_facts.append({"type": "completed_milestone", "count": 1, "evidence": f"{len(tasks_ai)} tasks extracted"})
                if any("#distract" in s.lower() or "#procrastin" in s.lower() for s in graph_seeds):
                    proxy_facts.append({"type": "distraction_event", "count": 1, "evidence": "tag detected"})

                markdown_body = ai_data.get("markdown_body", "")
                if "deep work" in markdown_body.lower() or "深度工作" in markdown_body:
                    proxy_facts.append({"type": "deep_work_session", "count": 1, "evidence": "keyword in markdown"})
                if "overtime" in markdown_body.lower() or "加班" in markdown_body:
                    proxy_facts.append({"type": "work_overtime", "count": 1, "evidence": "keyword in markdown"})

                if proxy_facts:
                    calc = scoring_engine.calculate_score("focus", proxy_facts)
                    engine_score = calc["score"]
                    ai_focus = float(focus)
                    delta = abs(ai_focus - engine_score)

                    if delta > 2.0:
                        logger.warning(f"[WARN] Score delta {delta:.1f}: AI={ai_focus}, Engine={engine_score}. Logging to growth_logs.")
                        try:
                            supabase.table("cortex_growth_logs").insert({
                                "decision_context": f"Focus scoring discrepancy on {ingest_date}",
                                "options_provided": {"ai_score": ai_focus, "engine_score": engine_score, "facts": proxy_facts},
                                "user_choice": str(engine_score),
                                "ai_prediction": str(ai_focus),
                                "prediction_match": False,
                                "lessons_learned": f"Focus delta={delta:.1f}. AI={ai_focus} vs Engine={engine_score}. Evidence: {calc['summary']}"
                            }).execute()
                        except Exception as _ge:
                            logger.warning(f"[WARN] growth_log write failed: {_ge}")
                    else:
                        logger.info(f"[OK] Scoring aligned (delta={delta:.1f}). AI={ai_focus}, Engine={engine_score}")
            except ImportError:
                logger.warning("[WARN] scoring_engine not found. Phase D skipped.")
            except Exception as _se:
                logger.warning(f"[WARN] Phase D scoring validation error: {_se}")
        # ---------------------------------------------------------------

        # 3. Local-First Storage Implementation
        import uuid

        import hashlib
        import os
        
        memory_id = str(uuid.uuid4())
        
        # 3.1 Generate embedding
        from app.services.embedder import generate_embedding
        content_for_embedding = ai_data.get("markdown_body") or request.content
        embedding = await generate_embedding(content_for_embedding)
        
        # 3.2 Write full content to local file (APPEND MODE - one file per day)
        local_filename = f"{ingest_date}.json"
        local_dir = "data/memories"
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, local_filename)
        
        current_time = get_current_iso_taipei()
        
        # Check if file exists (append mode)
        if os.path.exists(local_path):
            # Load existing memory for this day
            with open(local_path, "r", encoding="utf-8") as f:
                existing_memory = json.load(f)
            
            # Append new entry
            new_entry = {
                "time": current_time,
                "content": request.content,
                "ai_processed": ai_data.get("markdown_body"),
                "metadata": {
                    "mood": mood,
                    "focus": focus,
                    "energy": energy,
                    "tags": ai_data.get("tags") or [],
                    "is_ai": not request.skipAi,
                    "ai_model": model_name if not request.skipAi else "None",
                    "is_private": ai_data.get("is_private", False),
                    "category": ai_data.get("category", "Life"),
                    "facts": ai_data.get("facts", []),
                    "custom_metrics": ai_data.get("custom_metrics", {})
                }
            }
            
            existing_memory["entries"].append(new_entry)
            existing_memory["updated_at"] = current_time
            
            # Combine all content for full text
            all_content = "\n\n---\n\n".join([
                entry.get("content", "") for entry in existing_memory["entries"]
            ])
            existing_memory["combined_content"] = all_content
            
            full_memory = existing_memory
            logger.info(f"[OK] Appended to existing memory: {local_path} (now {len(existing_memory['entries'])} entries)")
        else:
            # First entry of the day
            full_memory = {
                "id": memory_id,
                "date": ingest_date,
                "entries": [{
                    "time": current_time,
                    "content": request.content,
                    "ai_processed": ai_data.get("markdown_body"),
                    "metadata": {
                        "mood": mood,
                        "focus": focus,
                        "energy": energy,
                        "tags": ai_data.get("tags") or [],
                        "is_ai": not request.skipAi,
                        "ai_model": model_name if not request.skipAi else "None",
                        "is_private": ai_data.get("is_private", False),
                        "category": ai_data.get("category", "Life"),
                        "facts": ai_data.get("facts", []),
                        "custom_metrics": ai_data.get("custom_metrics", {})
                    }
                }],
                "combined_content": request.content,
                "created_at": current_time,
                "updated_at": current_time
            }
            logger.info(f"[OK] Created new daily memory: {local_path}")
        
        # Write to file
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(full_memory, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[OK] Saved full content to local: {local_path}")
        
        # 3.3 Calculate content hash for integrity verification
        content_hash = hashlib.sha256(full_memory["combined_content"].encode()).hexdigest()
        
        # 3.4 Supabase payload: AI insights + metadata only (no full content)
        # Use combined AI insights from all entries
        combined_ai_insights = "\n\n---\n\n".join([
            entry.get("ai_processed", "") for entry in full_memory["entries"] if entry.get("ai_processed")
        ])
        
        
        # Determine the primary category & privacy flag from AI JSON
        is_private = ai_data.get("is_private", False)
        if request.skipAi: 
            # Default fallback for privacy: if no AI, assume private for safety
            is_private = True
            
        db_payload = {
            "date": ingest_date,  # Primary key for upsert
            "local_path": local_filename,
            "content_hash": content_hash,
            "ai_insights": combined_ai_insights or full_memory["combined_content"][:500],  # Fallback to preview
            "mood": mood,
            "focus": focus,
            "energy": energy,
            "is_ai": not request.skipAi,
            "ai_model": model_name if not request.skipAi else "None",
            "tags": ai_data.get("tags") or [],
            "updated_at": current_time,
            "is_private": is_private, # NEW: Privacy flag
            "category": ai_data.get("category", "Life"), # NEW: Life vs Project
            "facts": ai_data.get("facts", []), # NEW: List of fact-based objects
            "custom_metrics": ai_data.get("custom_metrics", {}) # NEW: Any other custom scores like Sleep
        }
        
        if embedding:
            db_payload["embedding"] = embedding
            logger.info(f"[OK] Generated {len(embedding)}-dim embedding")

        # 4. 寫入 Supabase (UPSERT - 一天一筆 for memories, standard insert for documents)
        if db:
            from app.core.database import safe_write
            try:
                if target_table == "memories":
                    # Upsert for memories (one entry per day)
                    response = safe_write(
                        db.table(target_table),
                        db_payload,
                        operation_type="upsert",
                        on_conflict="date"
                    )
                else:
                    # Generic Insert for documents
                    # Ensure metadata and title are handled for documents
                    doc_payload = {
                        "content": full_memory["combined_content"],
                        "title": ai_data.get("title") or f"Document {ingest_date}",
                        "url": ai_data.get("url"),
                        "doc_type": ai_data.get("doc_type", "note"),
                        "metadata": ai_data.get("meta", {}),
                        "embedding": embedding,
                        "tags": ai_data.get("tags", [])
                    }
                    response = db.table(target_table).insert(doc_payload).execute()
                
                logger.info(f"[OK] Stored in Supebase table: {target_table}")
                
            except Exception as e:
                logger.error(f"[ERROR] Supabase upsert failed: {e}")
                # 不中斷流程，本地檔案已存在
                check_res = db.table("memories").select("id").eq("date", ingest_date).execute()
                
                if check_res.data:
                    target_id = check_res.data[0]["id"]
                    logger.info(f"🔄 Entry for {ingest_date} exists (ID: {target_id}). Updating...")
                    update_payload = {k: v for k, v in db_payload.items() if k != "id"}
                    db.table("memories").update(update_payload).eq("id", target_id).execute()
                else:
                    db.table("memories").insert(db_payload).execute()
                    logger.info(f"✅ New memory stored for {ingest_date}.")

            # --- 5. Process Tasks (Action Items) ---
            # [v5.4 FIX] Moved OUT of except block — now always runs after any successful DB write
            try:
                tasks_list = ai_data.get("tasks", [])
                if tasks_list and target_table == "memories":
                    logger.info(f"📋 Found {len(tasks_list)} actionable items from AI. Processing...")
                    
                    # Pre-fetch Projects for Linking
                    proj_res = db.table("projects").select("id, name").execute()
                    proj_map = {p["name"].lower(): p["id"] for p in (proj_res.data or [])}
                    
                    # Get memory id for source linking
                    mem_res = db.table("memories").select("id").eq("date", ingest_date).execute()
                    memory_id_db = mem_res.data[0]["id"] if mem_res.data else None
                    
                    inserted_tasks = 0
                    for tk in tasks_list:
                        if not tk.get("title"):
                            continue
                        
                        proj_id = None
                        if tk.get("project"):
                            p_name = tk["project"].lower()
                            if p_name in proj_map:
                                proj_id = proj_map[p_name]
                            else:
                                # Auto-create new project referenced in diary
                                logger.info(f"Creating new project '{tk['project']}'...")
                                new_p = db.table("projects").insert({"name": tk["project"], "status": "active"}).execute()
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
                        try:
                            db.table("tasks").insert(task_payload).execute()
                            inserted_tasks += 1
                        except Exception as te:
                            logger.error(f"❌ Failed to insert task '{tk.get('title')}': {te}")
                    
                    logger.info(f"✅ Created {inserted_tasks}/{len(tasks_list)} tasks from diary.")
                else:
                    memory_id_db = None
                    if not tasks_list:
                        logger.info("ℹ️ No actionable tasks extracted from this diary entry.")

            except Exception as task_e:
                logger.error(f"❌ Task processing failed: {task_e}")
                memory_id_db = None

            # --- 6. Trigger Crystallization (Background) ---
            try:
                if not request.skipAi and memory_id_db:
                    logger.info(f"✨ Queueing crystallization for memory {memory_id_db}...")
                    background_tasks.add_task(
                        crystallizer.crystallize_memory, 
                        memory_id_db, 
                        ai_data.get("markdown_body", request.content), 
                        ingest_date
                    )
            except Exception as cryst_e:
                logger.warning(f"⚠️ Crystallization queue failed: {cryst_e}")


        # --- 7. Diary × Project Auto-Linking (P2/P3) ---
        link_result = {"completed_tasks": 0, "projects_linked": 0}
        if db and not request.skipAi:
            try:
                # We use the text generated by the AI block if possible so it has the clean tasks structure to check
                content_for_linking = ai_data.get("markdown_body", request.content)
                link_result = await auto_link_tasks_projects(content_for_linking, db, http_request)
                logger.info(f"🔗 Auto-link summary: +{link_result['completed_tasks']} tasks done, +{link_result['projects_linked']} projects linked.")
            except Exception as link_e:
                logger.warning(f"⚠️ Auto-link failed, skipping: {link_e}")

        # --- 8. Proactive Sovereign Insights ---
        sovereign_insights = None
        if db:
            try:
                # Fetch the latest context to report back to the Commander
                recon_res = db.table("cortex_context").select("*").order("last_updated", desc=True).limit(1).execute()
                if recon_res.data:
                    sovereign_insights = recon_res.data[0]
                    logger.info("📡 Sovereign Insights injected into response.")
            except Exception as recon_e:
                logger.warning(f"⚠️ Failed to fetch recon insights: {recon_e}")

        # 8. 回傳給前端
        return {
            "success": True,
            "status": "synced" if db else "kernel_only",
            "message": "Stored in DB and Kernel",
            "model": model_name,
            "data": ai_data,
            "link_result": link_result,
            "sovereign_insights": sovereign_insights
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"🔥 Ingest Critical Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))