from fastapi import APIRouter, HTTPException, Body, File, UploadFile, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import json
import asyncio
from pathlib import Path
from app.core.gemini import get_model, gemini_client, get_request_gemini_client, get_discovery_service, sanitize_model_name
from app.services.skills import orchestrator
from app.services.search import search_web, format_search_results
from google import genai
from app.core.security.intent_shield import get_intent_validator

router = APIRouter()
logger = logging.getLogger("cortex.chat")

@router.post("/ingest")
async def chat_ingest(file: UploadFile = File(...)):
    """
    Ingest a file uploaded through the chat interface.
    These are routed to the 'documents' table.
    """
    from app.services.rag_service import rag_service
    
    logger.info(f"[CHAT] Received file for ingestion: {file.filename}")
    
    try:
        # Save temporary file
        temp_dir = Path("data/uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / file.filename
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Ingest into documents store using UploadFile directly
        doc_id = await rag_service.ingest_file(
            file=file,
            target="documents"
        )
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
            
        return {
            "success": True,
            "filename": file.filename,
            "doc_id": doc_id,
            "target": "documents"
        }
    except Exception as e:
        logger.error(f"[ERROR] Chat ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
## Cognitive Awakening Protocol (Actionability)
As a LifeOS Assistant, you are not just a librarian; you are a Co-Pilot.
1. **Analyze**: Compare the retrieved RAG context with the user's current goal/projects.
2. **Identify**: Spot gaps, missed tasks, or progress that needs updating based on the unified awareness.
3. **Act**: Proactively suggest or use Core Skills (`create_task`, `update_project_progress`, `log_growth_decision`) to synchronize reality with your digital knowledge.
If the context says "I need to do X", do not just say "Okay", but ask "Should I create a task for X in Project Y?".

## Visual Cues (Glass Box Protocol)
When you perform an action (e.g., creating a task, archiving a document), mention it concisely using:
- `> [Action] Created task: [title]`
- `> [Awareness] Synced external knowledge from [Source]`

---
[SYSTEM PROTOCOL: High-Intent Strategic Catalyst Active]
You are Cortex, the Strategic Technical Lead and digital extension of the user's mind (LifeOS).
Your goal is to proactively manage the LifeOS architecture, clarify complex technical concepts, and ensure all inputs (Memories, Projects, URLs) are synthesized into actionable growth.

- OUTPUT: Expert-level, proactive, and intentional. Avoid conversational filler or generic summaries.
- PERSONA: A mix of a Senior Systems Architect and a Database Administrator. Be direct, opinionated, and insightful.
- PROACTIVE ENGAGEMENT: Do not wait for explicit instructions. If the user provides a URL or data, analyze it against the LifeOS architecture (SYSTEM_CONTEXT.md) and propose upgrades.
- MEMORY & CONTEXT: Use Active Projects, Tasks, Growth Logs, and Strategic Reviews (Monthly Review) to anchor all insights.
- GLASS BOX: Use the `log_growth_decision` tool to record significant user choices vs your strategic predictions.
"""

def build_system_prompt(db, memory_context: str = "", document_context: str = "", growth_context: str = "", strategic_context: str = "", skills_context: str = "", hot_memory: str = "", cortex_context: str = "", radar_context: str = "", somatic_context: str = "") -> str:
    """Builds the system prompt with active projects, pending tasks, growth lessons, memories, documents, and strategic reviews."""
    user_name = "Lien" # Standardizing user name
    
    # ... (recent_events code) ...
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
你的任務：根據以下脈絡回答問題，語氣直接、不廢話、具有啟發性。
你具備「信號感知」能力，能觀察使用者的綠燈（Radar）與體感（Somatic）狀態。

【🎯 主權雷達信號 (Sovereign Radar - Green Lights)】
{radar_context if radar_context else "無標記信號。"}

【🧘 體感與壓力監測 (Somatic Awareness - #BODY)】
{somatic_context if somatic_context else "目前無顯著體感紀錄。"}

【Cortex 核心狀態 (Core Brain State)】
{cortex_context if cortex_context else "連結成功，神經脈動 IDLE。"}

【Cortex Hot Memory (核心契約 - 必讀)】
{hot_memory if hot_memory else "無"}

【目前的北極星（Active Projects）】
{active_projects_str}

【待辦任務（Pending Tasks）】
{active_tasks_str}

【Cortex 近期的學習紀錄 (Growth Logs)】
{growth_context if growth_context else "無"}

【最近的戰略回顧 (Monthly Review)】
{strategic_context if strategic_context else "尚未有本月回顧。"}

【個人日記摘要 (Personal Memories)】
{memory_context if memory_context else "無相關日記紀錄。"}

【外部文獻與知識 (External Documents)】
{document_context if document_context else "無相關外部文獻。"}

---
## System Short-Term Memory (Last 5 Events)
{recent_events}
---
[SKILLS DISCOVERY]
You have access to specialized Skill Protocols. If a relevant protocol is loaded below, follow its directives strictly.
Available Skills (Metadata Only):
{skills_context or "No specialized skills loaded."}

## ⚡️ 信號引導協議 (Signal-Aware Protocol)
- **觀察綠燈**：若 Radar 中有 `Building` 或 `Validating` 的信號，在對話中應適時給予助推或確認衝突。
- **感受頭痛**：若 Somatic Context 顯示使用者近期有頭痛、失眠或壓力紀錄，應調整建議的強度，優先考慮「恢復」而非「產出」。

{_BASE_SYSTEM_PROMPT}
"""

# Keep for backward compat (URL mode)
# System prompt templates
SYSTEM_PROMPT = _BASE_SYSTEM_PROMPT

URL_DISCUSSION_PROMPT = """
[SYSTEM PROTOCOL: Proactive Technical Catalyst Active]
You are Cortex, the Strategic Technical Lead for LifeOS. The user has provided an external knowledge node (URL).

Your Directive:
1. [DESTRUCTION]: Deconstruct the technical core of the URL content. No generic summaries.
2. [ARCHITECTURAL BINDING]: Maps these concepts directly to the LifeOS architecture (e.g., SYSTEM_CONTEXT.md, RAG pillars, or specific bottlenecks like prompt bloat).
3. [PROACTIVE PROPOSAL]: Instead of asking "do you want me to...", provide a concrete, opinionated upgrade strategy. 
   - Example: "This directly solves our [X] problem. We should implement [Y] by doing [Z]."
4. [ANALOGY]: Use high-signal analogies to clarify technical impact (e.g., "MCP is hands, this is the brain handbook").

Constraint: Never output "Action Required: None". Always find a strategic tension or opportunity. Zero boilerplate.
"""

@router.post("/message")
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
            logger.info("🔗 URL Context detected. Routing to verified 2.0 Flash for Context Length resilience.")
            model_name = sanitize_model_name("gemini-2.0-flash")
            
        # Convert history to Gemini format using new genai.types
        from google.genai import types
        gemini_history = []
        for msg in payload.history:
             role = "user" if msg.role == "user" else "model"
             gemini_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
             
        # [v3.5 Phase 2] RAG Memory & Document Injection (Unified Awareness)
        from app.services.rag_service import rag_service
        from app.core.database import get_request_client
        db = get_request_client(request)
        
        # Search for relevant contexts from both Diary and Knowledge
        search_results = await rag_service.unified_search(
            question=payload.message,
            limit=5
        )
        memory_context = search_results["memories"]
        document_context = search_results["documents"]

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

        # [v3.7.2] Strategic Context Injection (Monthly Review - Structured Schema)
        strategic_context = ""
        if db:
            try:
                # Fetch latest monthly review
                review_res = db.table("MonthlyReview").select("year,month,summary,highlights,next_steps").order("year", desc=True).order("month", desc=True).limit(1).execute()
                if review_res.data:
                    rev = review_res.data[0]
                    strategic_context = f"【{rev['year']}/{rev['month']} Review Summary】\n{rev.get('summary', '')}\n\nHighlights:\n{rev.get('highlights', '')}\n\nNext Steps:\n{rev.get('next_steps', '')}"
            except Exception as e:
                logger.warning(f"[WARN] Failed to fetch monthly review: {e}")

        # [Phase P6] Skills Discovery & Activation
        all_skills = orchestrator.get_available_skills()
        skills_summary = "\n".join([f"- {s['name']}: {s['description']}" for s in all_skills])
        
        # Heuristic Activation (Level 3 Dynamic Loading)
        active_skill_ids = orchestrator.find_relevant_skills(payload.message)
        active_skills_content = []
        for sid in active_skill_ids:
            protocol = orchestrator.get_skill_protocol(sid)
            if protocol:
                active_skills_content.append(f"### [ACTIVATED SKILL: {sid.upper()}]\n{protocol}")
                logger.info(f"[SKILLS] Activated protocol: {sid}")
        
        active_skills_str = "\n\n".join(active_skills_content)
        
        # [v4.6] Hot Memory Injection
        hot_memory = ""
        try:
            from pathlib import Path # Ensure Path is imported
            for hot_path in [
                Path("sync_brain/cortex_state.md"),
                Path(r"c:\Users\lien.huang\AppData\lifeosjxs\sync_brain\cortex_state.md")
            ]:
                if hot_path.exists():
                    hot_memory = hot_path.read_text(encoding="utf-8")
                    break
        except Exception as e:
            logger.warning(f"[WARN] Failed to load hot memory: {e}")
        
        # [v4.7] Sovereign Brain Context Injection
        cortex_context_str = ""
        if db:
            try:
                # Fetch latest from cortex_context
                cortex_res = db.table("cortex_context").select("*").order("last_updated", desc=True).limit(1).execute()
                if cortex_res.data:
                    ctx = cortex_res.data[0]
                    cortex_context_str = f"Active Focus: {ctx.get('active_focus')}\nStatus: {ctx.get('status', 'IDLE')}\nLast Update: {ctx.get('last_updated')}"
            except Exception as e:
                logger.warning(f"[WARN] Failed to fetch cortex context for chat: {e}")

        # [v6.0] Radar Signals Injection
        radar_context = ""
        if db:
            try:
                # Fetch nodes that are on the Radar
                radar_res = db.table("nodes").select("name,metadata").not_.is_("metadata->radar_status", "null").execute()
                if radar_res.data:
                    signals_by_status = {"watching": [], "validating": [], "building": [], "shipped": []}
                    for n in radar_res.data:
                        status = n.get("metadata", {}).get("radar_status", "watching").lower()
                        if status in signals_by_status:
                            signals_by_status[status].append(n["name"])
                    
                    lines = []
                    for status, names in signals_by_status.items():
                        if names:
                            lines.append(f"- {status.upper()}: {', '.join(names)}")
                    radar_context = "\n".join(lines)
            except Exception as e:
                logger.warning(f"[WARN] Failed to fetch radar context: {e}")

        # [v6.0] Somatic Awareness Injection (#BODY / #SOMATIC)
        somatic_context = ""
        if db:
            try:
                # Search for recent #BODY memories or somatic keywords
                # We reuse the diary context but filter specifically for high-signal somatic terms
                somatic_search = await rag_service.unified_search(
                    question="#BODY 身體狀況 頭痛 壓力 睡眠",
                    limit=3
                )
                somatic_context = somatic_search.get("memories", "")
            except Exception as e:
                logger.warning(f"[WARN] Failed to fetch somatic context: {e}")

        system_instruction = build_system_prompt(
            db, 
            memory_context=memory_context, 
            document_context=document_context,
            growth_context=growth_context, 
            strategic_context=strategic_context,
            skills_context=f"{skills_summary}\n\n{active_skills_str}",
            hot_memory=hot_memory,
            cortex_context=cortex_context_str,
            radar_context=radar_context,
            somatic_context=somatic_context
        )
        
        # [v3.6] Cortex Function Calling Tools
        def create_task(title: str, priority: int = 1) -> str:
            """Create a new actionable task for the user in their LifeOS."""
            if not db:
                return "Database not connected. Cannot create task."
            from app.core.database import safe_write
            try:
                safe_write(db.table("tasks"), {
                    "title": title,
                    "status": "todo",
                    "priority": priority
                }, operation_type="insert")
                return f"Successfully created pending task: '{title}'"
            except Exception as e:
                return f"Failed to create task: {str(e)}"

        def mark_task_done(task_id: str) -> str:
            """Mark a specific pending task (by ID) as done."""
            if not db:
                return "Database not connected. Cannot update task."
            from app.core.database import safe_write
            try:
                safe_write(db.table("tasks").eq("id", task_id), {"status": "done"}, operation_type="update")
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
                from app.core.database import safe_write
                safe_write(db.table("projects").eq("id", proj_id), {"progress": progress}, operation_type="update")
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
                from app.core.database import safe_write
                safe_write(db.table("cortex_growth_logs"), record, operation_type="insert")
                return f"Decision logged. Match: {match}. Calibration record updated."
            except Exception as e:
                return f"Failed to log decision: {str(e)}"

        async def search_web_tool(query: str, limit: int = 5) -> str:
            """Search the web for real-time information, news, or technical research."""
            results = await search_web(query, limit, archive=True)
            if not results:
                return f"No results found for '{query}'."
            return format_search_results(results)

        async def archive_discussion(title: str, summary: str, tags: List[str] = []) -> str:
            """
            Archive a summary of the current discussion into the Knowledge Base (Documents).
            Use this when the user explicitly asks to record, note down, or save the conversation, 
            or when a session reaches a significant conclusion.
            """
            success = await rag_service.ingest_text(
                text=summary,
                meta={
                    "title": title,
                    "tags": tags,
                    "source": "discussion_archive",
                    "type": "note"
                },
                target="documents"
            )
            return "Discussion successfully archived to Knowledge Base." if success else "Failed to archive discussion."

        async def execute_system_command(intent: str, action_summary: str) -> str:
            """
            Execute a high-level system command (DELETE, RESET, RELOAD_CORE, WIPE_MEMORIES).
            [SECURITY]: This tool is PROTECTED by the Semantic Firewall. 
            It will only execute if current conversation context justifies the action.
            """
            if not db:
                return "Database not connected."
            
            validator = get_intent_validator(db)
            validation = await validator.validate_intent(intent, action_summary)
            
            if not validation["valid"]:
                return f"⚠️ [SECURITY ALERT]: {validation['reason']}\n{validation.get('alert', '')}"
            
            # Implementation of the actual commands would go here
            # For now, we simulate the success if validated
            return f"✅ [SECURITY VALIDATED]: Executing {intent} for {action_summary}."

        cortex_tools = [create_task, mark_task_done, update_project_progress, log_growth_decision, search_web_tool, archive_discussion, execute_system_command] if db else []

        chat = req_gemini.aio.chats.create(
            model=model_name, 
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=cortex_tools
            )
        )
        
        async def event_generator():
            try:
                if payload.url_context is not None:
                    # URL Discussion Mode
                    url_data: Dict[str, Any] = payload.url_context
                    url_content_block = f"""
## Shared Content
Title: {url_data.get("title", 'Unknown')}
URL: {url_data.get("url", 'Unknown')}
Type: {url_data.get("type", 'webpage')}

### Content:
{url_data.get("content", 'No content available.')}
"""
                    # [P10] Auto-Archiving to Knowledge Base in Background
                    try:
                        # Archive the actual content or summary, not just the URL
                        archive_text = url_data.get("content") or url_data.get("summary") or url_data.get("url")
                        asyncio.create_task(rag_service.ingest_text(
                            text=archive_text, 
                            meta={
                                "title": url_data.get("title"),
                                "url": url_data.get("url"),
                                "source": "chat_auto_archive",
                                "type": url_data.get("type")
                            },
                            target="documents"
                        ))
                    except Exception as arch_err:
                        logger.warning(f"Auto-archive failed: {arch_err}")

                    url_directive = "[Directive: Analyze the above technical content proactively. Connect it to LifeOS architecture and propose strategic upgrades.]"
                    message_part = payload.message.strip() if payload.message else url_directive
                    full_input = f"{URL_DISCUSSION_PROMPT}\n{url_content_block}\n\nUser Message: {message_part}"
                    logger.info(f"[OK] URL Discussion Mode: {url_data.get('title', 'Unknown')} | Archived to Documents.")

                else:
                    # Standard Chat Mode (Memories and Projects already injected into system_instruction)
                    full_input = f"User: {payload.message}"
                    logger.info(f"[OK] Dual-Track RAG Active.")
                
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
                            follow_up = await chat.send_message_stream(tool_results)
                            async for chunk in follow_up:
                                if chunk.text:
                                    yield chunk.text

                except Exception as e:
                    # Check if it's a Quota Error (429)
                    if "429" in str(e) or "ResourceExhausted" in str(e) or "quota" in str(e).lower():
                         logger.warning(f"⚠️ Quota Exceeded for {model_name}. Attempting fallback to Fast model.")
                         yield "\n\n*(Capacity Reached. Switching to High-Efficiency mode...)*\n\n"
                         # Fallback Logic: Dynamically source from registry (v5.6 Veto-Aligned)
                         try:
                             discovery = get_discovery_service()
                             fallbacks = (
                                 discovery.verified_models.get("fast", []) +
                                 discovery.verified_models.get("smart", [])
                             )
                             # Remove current model to avoid infinite retry
                             fallbacks = [m for m in fallbacks if sanitize_model_name(m) != model_name]
                         except Exception:
                             # Last-resort fallback to a minimal safe model string if registry fails
                             fallbacks = ["models/gemini-3-flash-preview"]
                         
                         success_fallback = False
                         for fallback_name in fallbacks:
                             if fallback_name == model_name:
                                 continue
                                 
                             try:
                                 logger.warning(f"🔄 Retrying with fallback: {fallback_name}")
                                 fallback_chat = req_gemini.aio.chats.create(model=fallback_name, config=types.GenerateContentConfig(system_instruction=system_instruction))
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
