
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import json
import asyncio
from pathlib import Path
from app.core.gemini import get_model, gemini_client, get_request_gemini_client
from google import genai

router = APIRouter()
logger = logging.getLogger("cortex.chat")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    model: Optional[str] = None
    url_context: Optional[Dict] = None  # {url, type, title, content} from url_fetch

# ---------------------------------------------------------------------------
# [Phase C] Short-Term Memory: inject last 5 evolution_log entries
# ---------------------------------------------------------------------------
_BASE_SYSTEM_PROMPT = """
[SYSTEM PROTOCOL: CodeSpeak Paradigm Active]
You are Cortex, the digital extension of the user's mind (LifeOS).
Your goal is to help the user manage their projects, clarify their thoughts, and retrieve memories with zero boilerplate.

- OUTPUT: High-signal, intentional, and concise. No conversational filler.
- FORMAT: Use structured Markdown.
- MEMORY ACCESS: You have access to the user's Memory Bank via the "## Relevant Context" section below.
- HALLUCINATION CONTROL: If the context is empty or says "NO MEMORIES FOUND", state exactly: "No relevant records found. Ask to create one."
- GLASS BOX: Expose your reasoning layer implicitly in your output structure. Use the `log_growth_decision` tool to record significant user choices vs your predictions.
"""

def build_system_prompt(db, memory_context: str = "", growth_context: str = "") -> str:
    """Builds the system prompt with active projects, pending tasks, growth lessons, memories, and short-term memory injected."""
    user_name = "Lien" # Standardizing user name
    
    recent_events = ""
    try:
        # Try both relative path and absolute fallback
        for evo_path in [
            Path("sync_brain/evolution_log.json"),
            Path(r"c:\Users\lien.huang\AppData\lifeosjxs\sync_brain\evolution_log.json")
        ]:
            if evo_path.exists():
                with open(evo_path, encoding="utf-8") as f:
                    logs = json.load(f)
                last5 = logs[-5:]
                recent_events = "\n".join(
                    f"- [{e.get('timestamp', '')[:10]}] [{e.get('type', '')}] {e.get('event', '')}: {e.get('description', '')[:120]}"
                    for e in last5
                )
                break
    except Exception as e:
        logger.warning(f"[WARN] Could not load evolution_log: {e}")

    # Fetch Active Projects
    active_projects_str = ""
    projects_map = {}
    if db:
        try:
            projects = db.table("projects").select("id,name,progress").eq("status", "active").execute().data
            if projects:
                for p in projects:
                    projects_map[p['id']] = p['name']
                active_projects_str = "\n".join(f"- {p['name']} (Progress: {p['progress']}%)" for p in projects)
            else:
                active_projects_str = "No active projects currently."
        except Exception as e:
            logger.warning(f"[WARN] Failed to fetch valid projects for prompt: {e}")
            active_projects_str = "Fetch error."
            
    # Fetch Active Tasks
    active_tasks_str = ""
    if db:
        try:
            tasks = db.table("tasks").select("id,title,project_id,priority").eq("status", "todo").execute().data
            if tasks:
                # Group by project name
                grouped_tasks = {}
                for t in tasks:
                    p_name = projects_map.get(t['project_id'], "Uncategorized / No Project")
                    if p_name not in grouped_tasks:
                        grouped_tasks[p_name] = []
                    grouped_tasks[p_name].append(t)
                
                lines = []
                for p_name, t_list in grouped_tasks.items():
                    lines.append(f"Project: {p_name}")
                    for t in t_list:
                        priority_mark = "🔥 " if t.get('priority', 0) > 1 else ""
                        lines.append(f"  - [ ] {priority_mark}{t['title']} (ID: {t['id']})")
                active_tasks_str = "\n".join(lines)
            else:
                active_tasks_str = "No pending tasks."
        except Exception as e:
            logger.warning(f"[WARN] Failed to fetch active tasks for prompt: {e}")
            active_tasks_str = "Fetch error."

    return f"""
你是 Cortex，{user_name} 的個人 AI 副駕。
你的任務：根據以下脈絡回答問題，語氣直接、不廢話、具有啟發性。若發現 {user_name} 的思考盲點，請直接點出。

【目前的北極星（Active Projects）】
{active_projects_str}

【待辦任務（Pending Tasks）】
{active_tasks_str}

【Cortex 近期的學習紀錄 (Growth Logs)】
{growth_context if growth_context else "無"}

【最相關的記憶片段】
{memory_context if memory_context else "無相關紀錄。您可以提議建立一個。"}

---
## System Short-Term Memory (Last 5 Events)
{recent_events}
---
{_BASE_SYSTEM_PROMPT}
"""

# Keep for backward compat (URL mode)
# System prompt templates
SYSTEM_PROMPT = _BASE_SYSTEM_PROMPT

URL_DISCUSSION_PROMPT = """
[SYSTEM PROTOCOL: URL CodeSpeak Extraction Active]
You are Cortex. The user has injected an external context node (URL).

Your Role:
1. [SYNTHESIS]: Extract raw signal / key ideas.
2. [MEMORY BINDING]: Connect to user context provided below.
3. [PROVOKATION]: Generate 2-3 sharp, tension-exposing questions.
4. [CONVERGENCE]: Output a concrete, actionable angle.

Constraint: Zero boilerplate. Direct reference. No generic summaries.
"""

@router.post("/chat")
async def stream_chat(request: Request, payload: ChatRequest):
    """Stream chat with Gemini, using per-user Gemini Key if provided via X-Gemini-Key header."""
    req_gemini = get_request_gemini_client(request)
    logger.info(f"💬 Chat Request: {payload.message}")
    
    try:
        model_config = get_model("smart")
        if not model_config.get("configured") or not req_gemini:
             raise HTTPException(status_code=503, detail="Cortex AI not configured (API Key missing)")

        from app.core.gemini import sanitize_model_name
        model_name = sanitize_model_name(payload.model or model_config.get("model"))
        
        # [v3.5 Phase 11] URL Discussion Model Interceptor
        # URL content easily exhausts Gemini 3 Pro (experimental) low tier quota
        # We intercept URL requests and route them to 1.5 Pro / Flash series which 
        # have 1M-2M context windows and proven 'summarization' capability parity 
        # with LifeOSvs-main.
        if payload.url_context and "gemini-3" in model_name:
            logger.info("🔗 URL Context detected. Routing to proven 1.5 Pro (via latest mapping) for Context Length resilience.")
            model_name = sanitize_model_name("gemini-1.5-pro")
            
        # Convert history to Gemini format using new genai.types
        from google.genai import types
        gemini_history = []
        for msg in payload.history:
             role = "user" if msg.role == "user" else "model"
             gemini_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
             
        # [v3.5 Phase 2] RAG Memory Injection
        from app.services.rag import hybrid_search, format_memories_for_context
        from app.core.database import get_supabase_client
        db = get_supabase_client(request)
        
        # Search for relevant memories before creating chat instance
        relevant_memories = await hybrid_search(
            query=payload.message,
            limit=5,
            similarity_threshold=0.4
        )
        memory_context = format_memories_for_context(relevant_memories)

        # [v3.6 P3] Semantic Growth Logs Injection
        growth_context = ""
        if db:
            try:
                from app.services.embedder import generate_embedding
                query_embedding = await generate_embedding(payload.message)
                if query_embedding:
                    res = db.rpc("match_growth_logs", {
                        "query_embedding": query_embedding,
                        "match_threshold": 0.4,
                        "match_count": 3
                    }).execute()
                    lessons = res.data or []
                    if lessons:
                        lines = []
                        for idx, l in enumerate(lessons):
                            lines.append(f"[{idx+1}] Context: {l.get('decision_context')} -> Lesson: {l.get('lessons_learned')}")
                        growth_context = "\n".join(lines)
            except Exception as e:
                logger.warning(f"[WARN] Failed to fetch growth logs: {e}")

        system_instruction = build_system_prompt(db, memory_context, growth_context)
        
        # [v3.6] Cortex Function Calling Tools
        def create_task(title: str, priority: int = 1) -> str:
            """Create a new actionable task for the user in their LifeOS."""
            if not db:
                return "Database not connected. Cannot create task."
            try:
                db.table("tasks").insert({
                    "title": title,
                    "status": "todo",
                    "priority": priority
                }).execute()
                return f"Successfully created pending task: '{title}'"
            except Exception as e:
                return f"Failed to create task: {str(e)}"

        def mark_task_done(task_id: str) -> str:
            """Mark a specific pending task (by ID) as done."""
            if not db:
                return "Database not connected. Cannot update task."
            try:
                db.table("tasks").update({"status": "done"}).eq("id", task_id).execute()
                return f"Task {task_id} marked as done."
            except Exception as e:
                return f"Failed to mark task done: {str(e)}"

        def update_project_progress(project_name: str, progress: int) -> str:
            """Update the completion progress percentage (0-100) of a specific active project."""
            if not db:
                return "Database not connected. Cannot update project."
            try:
                # Find project first
                res = db.table("projects").select("id").eq("name", project_name).execute()
                if not res.data:
                    return f"Project '{project_name}' not found."
                proj_id = res.data[0]["id"]
                db.table("projects").update({"progress": progress}).eq("id", proj_id).execute()
                return f"Project progress updated to {progress}%."
            except Exception as e:
                return f"Failed to update project: {str(e)}"

        def log_growth_decision(context: str, options: dict, choice: str, prediction: str = None, match: bool = None, lesson: str = None) -> str:
            """
            [Glass Box Protocol] Log an architectural or strategic decision. 
            Use this AFTER presenting a Decision Matrix or when the user makes a significant choice.
            """
            if not db:
                return "Database not connected. Cannot log decision."
            try:
                # 1. Build record
                record = {
                    "decision_context": context,
                    "options_provided": options,
                    "user_choice": choice,
                    "ai_prediction": prediction,
                    "prediction_match": match,
                    "lessons_learned": lesson
                }
                db.table("cortex_growth_logs").insert(record).execute()
                return f"Decision logged. Match: {match}. Calibration record updated."
            except Exception as e:
                return f"Failed to log decision: {str(e)}"

        cortex_tools = [create_task, mark_task_done, update_project_progress, log_growth_decision] if db else []

        chat = req_gemini.aio.chats.create(
            model=model_name, 
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=cortex_tools
            )
        )
        
        async def event_generator():
            try:
                if payload.url_context:
                    # URL Discussion Mode
                    url_data = payload.url_context
                    url_content_block = f"""
## Shared Content
Title: {url_data.get('title')}
URL: {url_data.get('url')}
Type: {url_data.get('type')}

### Content:
{url_data.get('content')}
"""
                    full_input = f"{URL_DISCUSSION_PROMPT}\n{url_content_block}\n\nUser: {payload.message}"
                    logger.info(f"[OK] URL Discussion Mode: {url_data.get('title')}")

                else:
                    # Standard Chat Mode (Memories and Projects already injected into system_instruction)
                    full_input = f"User: {payload.message}"
                    if relevant_memories:
                        logger.info(f"[OK] Injected {len(relevant_memories)} memories into context")
                    else:
                        logger.info("[INFO] No relevant memories found for this query")
                
                try:
                    response = await chat.send_message_stream(full_input)
                    
                    # [v3.6] Agentic Tool Call Execution Loop
                    # When Gemini emits function_calls, execute them and feed results back.
                    pending_tool_calls = []
                    async for chunk in response:
                        if chunk.text:
                            yield chunk.text
                        # Collect function calls emitted by Gemini
                        if hasattr(chunk, 'function_calls') and chunk.function_calls:
                            pending_tool_calls.extend(chunk.function_calls)

                    # Process any pending tool calls after the stream ends
                    if pending_tool_calls:
                        tool_map = {fn.__name__: fn for fn in cortex_tools}
                        tool_results = []
                        for fc in pending_tool_calls:
                            fn = tool_map.get(fc.name)
                            if fn:
                                logger.info(f"[Tool Call] Executing: {fc.name}({fc.args})")
                                try:
                                    if asyncio.iscoroutinefunction(fn):
                                        result_str = await fn(**fc.args)
                                    else:
                                        result_str = fn(**fc.args)
                                except Exception as te:
                                    result_str = f"Error: {str(te)}"
                                tool_results.append(
                                    types.Part.from_function_response(
                                        name=fc.name,
                                        response={"output": result_str}
                                    )
                                )
                                yield f"\n\n> **[Cortex Action]** `{fc.name}` → {result_str}\n"
                        
                        # Send tool results back to Gemini for a final reply
                        if tool_results:
                            follow_up = await chat.send_message_stream(
                                types.Content(role="tool", parts=tool_results)
                            )
                            async for chunk in follow_up:
                                if chunk.text:
                                    yield chunk.text

                except Exception as e:
                    # Check if it's a Quota Error (429)
                    if "429" in str(e) or "ResourceExhausted" in str(e) or "quota" in str(e).lower():
                         logger.warning(f"⚠️ Quota Exceeded for {model_name}. Attempting fallback to Fast model.")
                         yield "\n\n*(Capacity Reached. Switching to High-Efficiency mode...)*\n\n"
                         # Fallback Logic: Try a chain of verified models
                         fallbacks = [
                             sanitize_model_name("gemini-flash-lite-latest"),
                             sanitize_model_name("gemini-1.5-flash-latest"),
                         ]
                         
                         success_fallback = False
                         for fallback_name in fallbacks:
                             if fallback_name == model_name:
                                 continue
                                 
                             try:
                                 logger.warning(f"🔄 Retrying with fallback: {fallback_name}")
                                 fallback_chat = gemini_client.aio.chats.create(model=fallback_name, config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT))
                                 # We need to send the history manually since we are creating a new chat instance 
                                 # but for simplicity/speed in fallback we just push the full input
                                 fallback_resp = await fallback_chat.send_message_stream(full_input)
                                 
                                 async for chunk in fallback_resp:
                                     if chunk.text:
                                         yield chunk.text
                                         
                                 success_fallback = True
                                 break # Stop after first successful fallback
                             except Exception as fe:
                                 logger.error(f"❌ Fallback to {fallback_name} failed: {type(fe).__name__} - {str(fe)}")
                                 continue
                         
                         if not success_fallback:
                             logger.error("❌ ALL FALLBACKS EXHAUSTED. System is completely out of quota.")
                             yield f"\n\n[System Error: All available AI models are currently exhausted. Please try again in a few minutes or provide your own API Key in settings.]"
                    else:
                        raise e
                        
            except Exception as e:
                logger.error(f"Stream Error: {e}")
                yield f"\n\n[System Error: {str(e)}]"

        return StreamingResponse(event_generator(), media_type="text/plain")

    except Exception as e:
        logger.error(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
