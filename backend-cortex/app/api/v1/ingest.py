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

# LifeOS v7.1 Agentic Ingest Engine System Prompt
LIFEOS_V7_PROMPT = """
::: SYSTEM: LIFE OS AGENTIC INGEST v7.1 :::
<!-- 
⚠️ CRITICAL SYSTEM PROTOCOL ⚠️
此 Prompt 可自由修改邏輯與問句，但請務必保留 [Daily Metrics] 區塊的格式。
Python 後端依賴以下正則表達式來提取數據：
- Mood:\s*(\d+)
- Focus:\s*(\d+)
- Energy:\s*(\d+)
請確保輸出的 Markdown 中包含 "> - Mood: X" 這樣的行。
-->

# Role
你是 LifeOS 的核心處理單元（Agentic Ingest Engine）。
你的存在目的不是解釋、建議或引導使用者，而是作為一個「秩序維持與推進引擎」。

使用者負責：學習、思考、決策、選擇輸入內容
你負責：結構化、分類、關聯、推進、在必要時產生可執行行動

你的輸入是使用者一整天的原始紀錄（文字或語音轉錄）。
你的輸出是「標準 Markdown 格式」，包含豐富的排版與換行。
在 Markdown 的最後面，請務必按照協議附上一個隱藏的 JSON 數據區塊供系統解析。

# Core Directive
1. 結構化（Structure）：拆解為「Life」與「Project」雙軌。
   - **Project**: 任何具備目標、進度、技術性或經濟價值的外部產出行為。
   - **Life**: 內在感受、家庭互動、生理維持與純粹的社交。
2. 判斷（Judge）：區分純紀錄、訊號（Signal）、可行動（Actionable）。
3. 判定隱私（Privacy Check）：自動識別是否應進行隔離。
4. 推進（Advance）：任務目的是推進專案狀態。
5. 連結（Link）：自動識別專案、工具、人物、日期。

# Isolation Logic (Privacy Isolation)
你必須嚴格區分「家庭隔離」與「專案開發」：
- **Isolate (TRUE)**: 
  - 提及親友姓名或代稱（如：老婆、小孩、爸媽）。
  - 生理隱私（如：就醫細節、用藥、純粹的心情抒發）。
  - 家庭內部的衝突、瑣事或感性時刻。
  - **關鍵字觸發**: #private, #family, #secret, [隔離]
- **Synchronize (FALSE)**: 
  - 技術架構討論、程式碼片段、學習筆記。
  - 財報分析、市場研究、股票操作。
  - 具備具體 Target 或 Milestone 的執行過程。
  - 與外部團隊或開源社群的協作。

# Fact-Based Scoring (Evaluation Protocol)
你不再只是隨意給出分數，你必須提取「事實」來驅動評分：
1. **事實提取**：識別具體行為次數（如：深蹲 30 下、進入心流 2 次、被小孩中斷 1 次）。
2. **證據引用**：在評分旁標註你的證據來源。
3. **對抗性修正**：若使用者給出的自覺分數與事實矛盾，你必須以事實為準並說明原因。

# Processing Logic (Strict)
- 優先尋找使用者輸入中的「關鍵字」決定隔離狀態。
- 若內容混雜，優先以「保護隱私」為原則（設為 True）。
- 情緒、能量、專注度必須由事實（Facts）推導，若無事實支持，預設為 5.0。

# Output Format (Markdown Style)
請將分析結果整理為以下 Markdown 格式：

# [YYYY-MM-DD] 日記

> Daily Metrics
> - Mood: {{mood}} (Manual / Auto)
> - Focus: {{focus}} (Manual / Auto)
> - Energy: {{energy}} (Manual / Auto)
> - Time Ratio: 🔧 / 🌊
> - Action Check:
> - Drift Point:

## 1. Highlights
- Day Summary: 
- Signals Detected:

## 2. Gratitude (若有)

## 3. Reflection
- Behavior Path: (列表)
- Anti-Cognitive Closure: 
- Blind Spot Question:
- Self-Deception Trigger:

### 強制五欄位模組
[Day Summary] / [Signals Detected] / [Behavior Path] / [Drift Point] / [Blind Spot Question]

## 4. Tomorrow’s MIT
- (Most Important Task)

## 5. Action Tip

## 6. Cognitive Lens Reframing
- Model/Concept:
- Reframe:

## 7. Tags (JSON tags 欄位亦須包含)

## Graph Seeds
(列出 #Tag, [[Link]], @Person)

---

### Machine Processing Protocol (Hidden)
請在輸出的 **最後面**，附上一個 JSON 區塊，包含所有提取的元數據。
格式如下（請確保 JSON 格式合法）：
```json
{
  "mood": 5,
  "focus": 5,
  "energy": 5,
  "category": "Life",
  "tags": ["tag1", "tag2"],
  "projects": ["Project Name A", "Project Name B"],
  "is_private": true,
  "facts": [
    {"type": "deep_work_session", "count": 1, "evidence": "描述內容"}
  ],
  "custom_metrics": {
      "Sleep": 8
  }
}
```
這個區塊將被系統自動截取並存入資料庫，不會顯示給使用者。
"""

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
1. `completed_task_ids`: 從待辦清單中，找出使用者在日記中暗示他已經完成的任務 ID。（注意：必須是明確完成，如果只是「正在做」或「準備做」則不要納入）。
2. `mentioned_project_ids`: 從專案清單中，找出使用者在日記中提到的專案 ID。

僅回傳匹配到的 ID 字串陣列。若無任何匹配，回傳空陣列 []。
"""
        model_name = "gemini-2.0-flash"
        from app.core.gemini import safe_generate_content
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
        if result_str:
            result = json.loads(result_str)
            completed_ids = result.get("completed_task_ids", [])
            mentioned_ids = result.get("mentioned_project_ids", [])
            
            # 3. Update DB
            logger = logging.getLogger("cortex.api.ingest.autolink")
            
            # 3.1 Mark tasks done
            from app.core.database import safe_write
            for t_id in completed_ids:
                safe_write(db.table("tasks").eq("id", t_id), {"status": "done"}, operation_type="update")
                logger.info(f"Task marked done via auto-link: {t_id}")
                
            # 3.2 Update projects updated_at (to bubble them up as "focused")
            from app.core.utils import get_current_iso_taipei
            linked_project_names = []
            
            for p_id in mentioned_ids:
                # Get the project name for the UI toast
                p_name = next((p["name"] for p in active_projects if p["id"] == p_id), "未知專案")
                if p_name != "未知專案":
                    linked_project_names.append(p_name)
                    
                safe_write(db.table("projects").eq("id", p_id), {"updated_at": get_current_iso_taipei()}, operation_type="update")
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
            user_context = (
                f"[SYSTEM INSTRUCTION]\n"
                f"1. DATE: The target date for this log is {ingest_date}. You MUST replace [YYYY-MM-DD] in your output (Header and Graph Seeds) with {ingest_date}.\n"
                f"2. METRICS: Examine the user's log. IF it contains a '> Daily Metrics' block with 'Mood: X', 'Focus: Y', 'Energy: Z', you MUST EXPLICITLY use those exact numbers in the JSON output meta.metrics. Do not auto-calculate them if the user provided them (Manual).\n\n"
            )
            prompt = f"{LIFEOS_V7_PROMPT}\n\n{user_context}[USER LOG - {ingest_date}]:\n{request.content}\n\n[HABITS LOGGED]:\n{', '.join(habits_list) if habits_list else 'None'}"
            
            # 2. Call Gemini API via Safe Failover Protocol
            try:
                from app.core.gemini import safe_generate_content
                response = await safe_generate_content(
                    client=req_gemini,
                    prefer_mode="fast",
                    contents=prompt
                )
                
                logger.info("[OK] Gemini raw generation returned.")
                response_text = response.text.strip()
                
                import re
                import json
                
                # [v3.8.8 Fix] Improved Parsing: Extract JSON and keep Markdown separately
                # gemini-2.0-flash-lite often mixes both.
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if not json_match:
                    # Fallback to loose JSON search
                    json_match = re.search(r'(\{.*?\})', response_text, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1)
                    # The rest is markdown
                    # We remove the JSON block from the response to get the clean markdown
                    markdown_part = response_text.replace(json_match.group(0), "").strip()
                    # Also strip any trailing/leading md code fences if they were wrapping the whole thing
                    markdown_part = re.sub(r'^```markdown\s*', '', markdown_part)
                    markdown_part = re.sub(r'\s*```$', '', markdown_part)
                    
                    try:
                        ai_data = json.loads(json_str)
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
        metrics = meta.get("metrics") or {}
        mood = metrics.get("mood", 5)
        focus = metrics.get("focus", 5)
        energy = metrics.get("energy", 5)
        
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

        # 8. 回傳給前端
        return {
            "success": True,
            "status": "synced" if db else "kernel_only",
            "message": "Stored in DB and Kernel",
            "model": model_name,
            "data": ai_data,
            "link_result": link_result
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"🔥 Ingest Critical Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))