# 檔案位置: backend-cortex/app/api/v1/ingest.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import json
import datetime

# 引入核心模組
from app.core.gemini import get_model, get_embeddings
from app.core.database import supabase
from app.core.time_utils import get_today_str_taipei, get_current_iso_taipei

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

# 定義請求格式
class IngestRequest(BaseModel):
    content: str
    date: Optional[str] = None  # YYYY-MM-DD
    habits: Optional[List[str]] = []
    skipAi: bool = False
    mode: str = "append"

@router.post("/ingest") 
async def ingest_log(request: IngestRequest):
    # Default date if missing
    ingest_date = request.date or get_today_str_taipei()
    habits_list = request.habits or []
    
    logger.info(f"🧠 Cortex receiving input for {ingest_date} (Skip AI: {request.skipAi})...")
    
    try:
        # 1. 呼叫 Gemini with v7.1 Prompt (Unless skipped)
        import google.generativeai as genai
        
        model_config = get_model("fast") # Use FAST model for ingest speed
        ai_data: Dict[str, Any] = {}
        model_name = model_config.get("model")

        # Skip AI if requested
        if not request.skipAi and model_config.get("configured"):
            # 初始化模型物件
            model = genai.GenerativeModel(model_name)
            
            # 構建使用者輸入 (注入 Today 作為基準日期)
            user_content = f"""
[Reference] Today is: {get_today_str_taipei()}
Target Date: {ingest_date}
Habits Tracked: {', '.join(habits_list) if habits_list else 'None'}

User's Daily Log:
{request.content}
"""
            
            # 使用 v7.1 System Prompt
            full_prompt = f"{LIFEOS_V7_PROMPT}\n\n{user_content}\n\n請嚴格按照上述格式輸出 JSON。"
            
            try:
                response = model.generate_content(full_prompt)
                
                # 2. 解析 JSON
                response_text = response.text.strip()
                # Robust JSON extraction
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
                ai_data = json.loads(response_text)
                if not isinstance(ai_data, dict):
                    ai_data = {}
            except Exception as e:
                logger.error(f"Gemini/JSON Error: {e}")
                ai_data = {}
        elif request.skipAi:
            logger.info("⏩ AI Generation skipped by user request.")
        else:
             logger.warning("Gemini API Key not set, using mock response")

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

        # 1. Date Detection (Robust)
        meta = ai_data.get("meta") or {}
        detected_date = meta.get("date")
        if detected_date:
            import re
            if re.match(r'^\d{4}-\d{2}-\d{2}$', str(detected_date)):
                logger.info(f"📅 AI date detection Signal: {detected_date}")
                ingest_date = str(detected_date)
            else:
                logger.warning(f"⚠️ AI returned non-standard date format: {detected_date}")

        # 2. Metrics Extraction (Robust)
        metrics = meta.get("metrics") or {}
        mood = metrics.get("mood", 5)
        focus = metrics.get("focus", 5)
        energy = metrics.get("energy", 5)

        # ---------------------------------------------------------------
        # [Phase D] Scoring Engine Validation — AI Bias Detection
        # Compare AI-assigned focus score against fact-based calculation.
        # If delta > 2.0, log as a discrepancy to cortex_growth_logs.
        # ---------------------------------------------------------------
        if not request.skipAi and ai_data:
            try:
                import sys, os as _os
                # Resolve scoring_engine path (tools/ or sync_brain/)
                _base = r"c:\Users\lien.huang\AppData\lifeosjxs"
                for _spath in [
                    _os.path.join(_base, "tools"),
                    _os.path.join(_base, "sync_brain"),
                ]:
                    if _spath not in sys.path:
                        sys.path.insert(0, _spath)

                from scoring_engine import engine as scoring_engine

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
                        if supabase:
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
        if supabase:
            try:
                # Upsert: 如果日期已存在則更新，否則新增
                response = supabase.table("memories").upsert(
                    db_payload,
                    on_conflict="date"  # 以 date 為唯一鍵
                ).execute()
                
                logger.info(f"[OK] Upserted memory to Supabase for date: {ingest_date}")
                
            except Exception as e:
                logger.error(f"[ERROR] Supabase upsert failed: {e}")
                # 不中斷流程，本地檔案已存在
                check_res = supabase.table("memories").select("id").eq("date", ingest_date).execute()
                
                if check_res.data:
                    # 已存在：更新
                    target_id = check_res.data[0]["id"]
                    logger.info(f"🔄 Entry for {ingest_date} exists (ID: {target_id}). Updating...")
                    update_payload = {k: v for k, v in db_payload.items() if k != "id"}
                    supabase.table("memories").update(update_payload).eq("id", target_id).execute()
                else:
                    # 不存在：新增
                    supabase.table("memories").insert(db_payload).execute()
                    logger.info(f"✅ New memory stored for {ingest_date}.")
                        
                # --- 5. Process Tasks (Action Items) ---
                # Added in v7.1: Connect AI Tasks to DB
                tasks_list = ai_data.get("tasks", [])
                if tasks_list:
                    logger.info(f"📋 Found {len(tasks_list)} actionable items. Processing...")
                    
                    # 5.1 Pre-fetch Projects for Linking
                    # optimization: fetch all project names to map (name -> id)
                    # We use a simple case-insensitive match
                    project_map = {}
                    try:
                        p_res = supabase.table("projects").select("id, name").execute()
                        if p_res.data:
                            for p in p_res.data:
                                project_map[p["name"].lower()] = p["id"]
                    except Exception as pe:
                        logger.warning(f"Could not fetch projects for linking: {pe}")

                    # 5.2 Construct Task Payloads
                    new_tasks = []
                    target_memory_id = target_id if 'target_id' in locals() else None 
                    
                    # Fix: Capture ID on insert
                    if not target_memory_id:
                        # We just inserted. Let's fetch it back.
                        rec_res = supabase.table("memories").select("id").eq("date", ingest_date).execute()
                        if rec_res.data:
                            target_memory_id = rec_res.data[0]["id"]

                    for t in tasks_list:
                        task_title = t.get("title")
                        if not task_title: continue
                        
                        proj_name = t.get("project")
                        proj_id = None
                        if proj_name and isinstance(proj_name, str):
                            proj_id = project_map.get(proj_name.lower())
                        
                        new_tasks.append({
                            "title": task_title,
                            "status": "todo",
                            "project_id": proj_id,
                            "source_memory_id": target_memory_id,
                            "due_date": ingest_date, # Default to today/ingest date
                            "priority": 1
                        })

                    # 5.3 Sort & Insert
                    if new_tasks:
                        try:
                            supabase.table("tasks").insert(new_tasks).execute()
                            logger.info(f"✅ Successfully created {len(new_tasks)} tasks in DB.")
                        except Exception as te:
                            logger.error(f"❌ Failed to insert tasks: {te}")

            except Exception as db_e:
                logger.error(f"❌ Database Operation Failed: {db_e}")

        # 4. 回傳給前端
        return {
            "success": True,
            "model": model_name,
            "data": ai_data
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"🔥 Ingest Critical Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))