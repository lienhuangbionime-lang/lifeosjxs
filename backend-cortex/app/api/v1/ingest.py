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

# Role

你是 LifeOS 的核心處理單元（Agentic Ingest Engine）。

你的存在目的不是解釋、建議或引導使用者，
而是作為一個「秩序維持與推進引擎」。

使用者負責：
- 學習
- 思考
- 決策
- 選擇輸入內容

你負責：
- 結構化
- 分類
- 關聯
- 推進
- 在必要時產生可執行行動

你的輸入是使用者一整天的原始紀錄（文字或語音轉錄）。
你的輸出是結構化 JSON，用於：
- 圖譜視覺化
- 專案狀態推進
- Google Tasks 自動化

# Core Directive

1. 結構化（Structure）
- 所有輸入必須拆解為「Life」與「Project」雙軌
- 不得混合敘述

2. 判斷（Judge）
- 區分：
  a. 純紀錄
  b. 訊號（Signal）
  c. 可行動（Actionable）
- 只有同時滿足以下條件者，才可進入 tasks：
  • 行為具體
  • 可由單一人完成（即使用者）
  • 與時間或專案推進存在明確關聯
- 模糊、情緒性、尚未成形的想法 → # idea_seeds 為內部分類概念，不得作為輸出欄位

3. 推進（Advance）【NEW】
- 任務的目的不是「完成清單」，而是「推進專案狀態」
- 若某任務無法對任何專案狀態產生變化，預設不得生成

4. 連結（Link）
- 自動識別專案、工具、人物、日期
- 僅建立可回溯的 Tag 與 Graph Nodes
- 不得解釋關聯意義

Graph Seeds（唯一允許的連結層）
• 僅做標記，不做解釋
• 類型包含：
  • #Tag
  • [[YYYY-MM-DD]]
  • 關聯物件（人 / 工具 / 專案 / 地點）

# Processing Logic

在生成任何輸出（Markdown 與 JSON）前，你必須完成以下內部檢核：

1. 情緒與能量僅作為「數據標註」，不可用於推論動機
2. 每一個專案必須確認其狀態：
   - 新專案 / 進行中 / 停滯 / 收斂中
3. 每一個潛在任務必須回答：
   - 這是行動，還是焦慮的語言殘留？
   - 不確定 → 不生成

# Hard Constraints

1. 主權原則（Interpretation Ownership）
• 所有詮釋權屬於使用者
• 你只能整理、對齊、顯影
• 禁止任何形式的人格評價、成熟度判斷、成長敘事

2. 時間真實性（Temporal Fidelity v2）
• 僅能基於實際發生的行為
• 不得推論「應該 / 可能 / 代表」
• 行為時間允許使用「區間估計」，但必須明確標示為估計

3. 顆粒度守恆（Granularity Conservation）
• 不得將多個行為壓縮為抽象描述
• 強制順序：行為 → 時間 → 類別
• 不得用心理狀態取代行為紀錄

4. 反幻覺保全（Anti-Hallucination）
• 不存在的行為 = 不得補齊
• 模糊 = 保留模糊
• 不確定 = 明確標示為不確定
• 禁止合理腦補

5. 行動主權隔離（Action Sovereignty）
- 任務是系統的推進判斷，不是使用者的承諾
- 不得使用任何語言暗示「你應該」

⸻

固定執行協議（Protocol）

A. 數據對齊（Alignment）
• Mood / Focus / Energy：1–10 分
• 允許填寫數值
• 禁止情緒形容詞與心理歸因
• 若 Mood < 7 且 Focus < 5 → 標記 WARNING（不解釋）
• 【授權條款】若使用者未明示分數，且當日行為記錄總時數 ≥ 30 分鐘，允許系統基於「實際行為密度與持續性」自動填寫分數，並在分數後標註來源為（Auto｜Behavior-Based）

B. 行為顆粒度（Behavior Path）
• 每一行格式強制為：

行為描述 [T:區間]（估） (S/A)

• 類別定義：
  • (S) 造船 / 工具 / 系統 / 調校
  • (A) 航行 / 實作 / 陪伴 / 產出
• 禁止使用精確分鐘，除非使用者原文提供
• 行為時間若以區間估計呈現，仍可用於 Alignment 分數計算，但不得用於心理或動機推論

C. 情感穩定度（F-Score）
• 僅記錄「高品質家庭連結次數」
• 不延伸意義、不評價好壞、不做心理推論

D. 偏誤掃描（Bias Scan · Hard Gate）
• 僅在使用者原文中明確出現行為時才可標示
• 標示必須使用固定句型：

- 偏誤名稱（來自：原文中之具體行為描述）

• 禁止使用：
  • 可能
  • 跡象
  • 傾向
  • 感覺

E. 實作核取（Action Check）
• 行為實作 > 10 分鐘 → ✅
• 僅規劃 / 調整工具 → ⚠️

F. 嚴格一致性（Strict Consistency）【CRITICAL】
• Markdown 中的 > Daily Metrics 分數必須與 JSON 中的 meta.metrics 完全一致。
• 【日期權重第一優先級】：若使用者在日誌內容（content）中明確提到了一個特定的日期（例如「2/1」或「二月一號」），則 JSON 的 meta.date 必須反映該日期（YYYY-02-01），而不是系統傳入的 Date 變數。

⸻

輸出格式（不可破壞）

你必須輸出一個 JSON 物件，包含以下欄位：

{
  "markdown_body": "完整的日記 Markdown 內容，格式如下",
  "meta": {
    "date": "YYYY-MM-DD",
    "metrics": {
      "mood": 5,
      "focus": 5,
      "energy": 5,
      "mood_source": "Manual/Auto",
      "focus_source": "Manual/Auto",
      "energy_source": "Manual/Auto"
    }
  },
  "tasks": [
    {"title": "具體任務描述", "status": "PENDING", "project": "專案名稱或null"}
  ],
  "tags": ["tag1", "tag2"],
  "graph_seeds": ["[[2024-01-01]]", "#project-name", "@person-name"]
}

Markdown 結構固定如下，不可增減欄位：

# [YYYY-MM-DD] 日記

> Daily Metrics
> - Mood: X (Manual/Auto)
> - Focus: X (Manual/Auto)
> - Energy: X (Manual/Auto)
> - Time Ratio: 🔧 X% / 🌊 X%
> - Action Check: ✅/⚠️
> - Drift Point: 描述或「無」

## 1. Highlights
- Day Summary: 一句話總結
- Signals Detected: 重要訊號或「無」

## 2. Gratitude
列出感恩事項或「今日無特別記錄」

## 3. Reflection
- Behavior Path: 行為列表（格式：行為 [T:區間]（估） (S/A)）
- Anti-Cognitive Closure: 未解問題
- Blind Spot Question: 盲點提問
- Self-Deception Trigger: 自欺觸發點或「無」

## 4. Tomorrow's MIT
最重要的 1-3 件事

## 5. Action Tip
句話行動建議

## 6. Cognitive Lens Reframing
- Model/Concept: 使用的思維模型
- Reframe: 重新框架的觀點

## 7. Tags
#tag1 #tag2

## Graph Seeds
[[YYYY-MM-DD]] #project @person

⸻

記住：你是秩序引擎，不是心理諮商師。
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
        model = gemini.models.get(model="gemini-2.0-flash")
        resp = gemini.models.generate_content(
            model="gemini-2.0-flash",
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
            for t_id in completed_ids:
                db.table("tasks").update({"status": "done"}).eq("id", t_id).execute()
                logger.info(f"Task marked done via auto-link: {t_id}")
                
            # 3.2 Update projects updated_at (to bubble them up as "focused")
            from app.core.utils import get_current_iso_taipei
            linked_project_names = []
            
            for p_id in mentioned_ids:
                # Get the project name for the UI toast
                p_name = next((p["name"] for p in active_projects if p["id"] == p_id), "未知專案")
                if p_name != "未知專案":
                    linked_project_names.append(p_name)
                    
                db.table("projects").update({"updated_at": get_current_iso_taipei()}).eq("id", p_id).execute()
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
    habits: Optional[List[str]] = []
    skipAi: bool = False
    mode: str = "append"

@router.post("")
@router.post("/")
async def ingest_log(http_request: Request, request: IngestRequest, background_tasks: BackgroundTasks):
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
            
            # 2. Call Gemini API — using correct google.genai SDK syntax
            try:
                # Based on google.genai, we use client.models.generate_content(model=..., contents=...)
                response = req_gemini.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                
                logger.info("[OK] Gemini raw generation returned.")
                response_text = response.text.strip()
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
                
                try:
                    ai_data = json.loads(response_text)
                    if not isinstance(ai_data, dict):
                        ai_data = {}
                    logger.info("[OK] Gemini JSON parsing complete.")
                except json.JSONDecodeError as je:
                    logger.error(f"[ERROR] Gemini JSON Decode Error: {je}. Raw output snippet: {response_text[:100]}")
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
                    "ai_model": model_name if not request.skipAi else "None"
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
                        "ai_model": model_name if not request.skipAi else "None"
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
            "updated_at": current_time
        }
        
        if embedding:
            db_payload["embedding"] = embedding
            logger.info(f"[OK] Generated {len(embedding)}-dim embedding")

        # 4. 寫入 Supabase (UPSERT - 一天一筆)
        if db:
            try:
                # Upsert: 如果日期已存在則更新，否則新增
                response = db.table("memories").upsert(
                    db_payload,
                    on_conflict="date"  # 以 date 為唯一鍵
                ).execute()
                
                logger.info(f"[OK] Upserted memory to Supabase for date: {ingest_date}")
                
            except Exception as e:
                logger.error(f"[ERROR] Supabase upsert failed: {e}")
                # 不中斷流程，本地檔案已存在
                check_res = db.table("memories").select("id").eq("date", ingest_date).execute()
                
                if check_res.data:
                    # 已存在：更新
                    target_id = check_res.data[0]["id"]
                    logger.info(f"🔄 Entry for {ingest_date} exists (ID: {target_id}). Updating...")
                    update_payload = {k: v for k, v in db_payload.items() if k != "id"}
                    db.table("memories").update(update_payload).eq("id", target_id).execute()
                else:
                    # 不存在：新增
                    db.table("memories").insert(db_payload).execute()
                    logger.info(f"✅ New memory stored for {ingest_date}.")
                        
                # --- 5. Process Tasks (Action Items) ---
                # Added in v7.1: Connect AI Tasks to DB
                tasks_list = ai_data.get("tasks", [])
                if tasks_list:
                    logger.info(f"📋 Found {len(tasks_list)} actionable items. Processing...")
                    
                    # 5.1 Pre-fetch Projects for Linking
                    # optimization: fetch all project names to map (name -> id)
                    # We use a simple case-insensitive match
                    logger.info("Fetching existing projects for linking...")
                    proj_res = db.table("projects").select("id, name").execute()
                    proj_map = {p["name"].lower(): p["id"] for p in (proj_res.data or [])}
                    
                    # Also need the memory id we just created/updated
                    mem_res = db.table("memories").select("id").eq("date", ingest_date).execute()
                    memory_id_db = mem_res.data[0]["id"] if mem_res.data else None
                    
                    inserted_tasks = 0
                    for tk in tasks_list:
                        if not tk.get("title"): continue
                        
                        # Find project id
                        proj_id = None
                        if tk.get("project"): # Changed from project_name to project based on original ai_data structure
                            p_name = tk["project"].lower()
                            if p_name in proj_map:
                                proj_id = proj_map[p_name]
                            else:
                                # Create new project
                                logger.info(f"Creating new project '{tk['project']}'...")
                                new_p = db.table("projects").insert({"name": tk["project"], "status": "active"}).execute()
                                if new_p.data:
                                    proj_id = new_p.data[0]["id"]
                                    proj_map[p_name] = proj_id
                                    
                        # Insert task
                        task_payload = {
                            "title": tk["title"],
                            "status": "todo",
                            "priority": tk.get("priority", 1), # Assuming priority might be in task dict
                            "project_id": proj_id,
                            "source_memory_id": memory_id_db
                        }
                        try:
                            db.table("tasks").insert(task_payload).execute()
                            inserted_tasks += 1
                        except Exception as te:
                            logger.error(f"❌ Failed to insert task '{tk.get('title')}': {te}")
                    
                    if inserted_tasks > 0:
                        logger.info(f"✅ Successfully created {inserted_tasks} tasks in DB.")
                    else:
                        logger.info("No new tasks were inserted.")

                # --- 6. Trigger Crystallization (Background) ---
                if not request.skipAi and memory_id_db:
                    logger.info(f"✨ Queueing crystallization for memory {memory_id_db}...")
                    background_tasks.add_task(
                        crystallizer.crystallize_memory, 
                        memory_id_db, 
                        ai_data.get("markdown_body", request.content), 
                        ingest_date
                    )

            except Exception as db_e:
                logger.error(f"❌ Database Operation Failed: {db_e}")

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