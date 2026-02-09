# 檔案位置: backend-cortex/app/api/v1/ingest.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import json
import datetime

# 引入核心模組
from app.core.gemini import get_model
from app.core.database import supabase
from app.models.schemas import LogEntrySchema 

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
一句話行動建議

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
    text: str
    date: str  # YYYY-MM-DD
    habits: Optional[List[str]] = []
    skip_ai: Optional[bool] = False

@router.post("/ingest") 
async def ingest_log(request: IngestRequest):
    logger.info(f"🧠 Cortex receiving input for {request.date} (Skip AI: {request.skip_ai})...")
    
    try:
        # 1. 呼叫 Gemini with v7.1 Prompt (Unless skipped)
        import google.generativeai as genai
        
        model_config = get_model("smart")
        ai_data = None
        model_name = model_config.get("model", "gemini-2.5-flash")

        # Skip AI if requested
        if not request.skip_ai and model_config.get("configured"):
            # 初始化模型物件
            model = genai.GenerativeModel(model_name)
            
            # 構建使用者輸入
            user_content = f"""
Date: {request.date}
Habits Tracked: {', '.join(request.habits) if request.habits else 'None'}

User's Daily Log:
{request.text}
"""
            
            # 使用 v7.1 System Prompt
            full_prompt = f"{LIFEOS_V7_PROMPT}\n\n{user_content}\n\n請嚴格按照上述格式輸出 JSON。"
            
            try:
                response = model.generate_content(full_prompt)
                
                # 2. 解析 JSON
                text = response.text.strip()
                # Robust JSON extraction
                import re
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    text = json_match.group(0)
                ai_data = json.loads(text)
                if not isinstance(ai_data, dict):
                    raise ValueError("AI response is not a valid JSON object")
            except Exception as e:
                logger.error(f"Gemini/JSON Error: {e}")
                # Safe checking of response text
                try: 
                    if 'response' in locals():
                         # Check if response was blocked or has no text
                         if response.parts:
                             logger.error(f"Raw response text (first 500 chars): {response.text[:500]}")
                         else:
                             logger.error(f"Response blocked or empty: {response.prompt_feedback}")
                except Exception as log_err:
                    logger.error(f"Could not retrieve response details: {log_err}")
        elif request.skip_ai:
            logger.info("⏩ AI Generation skipped by user request.")
        else:
             logger.warning("Gemini API Key not set, using mock response")

        if ai_data is None:
            # Fallback to basic structure
            ai_data = {
                "markdown_body": f"# [{request.date}] 日記\n\n{request.text}", 
                "meta": {
                    "date": request.date,
                    "metrics": {"mood": 5, "focus": 5, "energy": 5}
                }, 
                "tasks": [],
                "tags": [],
                "graph_seeds": []
            }

        # 3. 寫入海馬迴 (Supabase)
        import uuid
        
        # Prepare Meta field (merge graph_seeds into meta for storage)
        meta_payload = ai_data.get("meta", {})
        if not isinstance(meta_payload, dict):
            meta_payload = {}
            
        if "graph_seeds" in ai_data:
            meta_payload["graphSeeds"] = ai_data["graph_seeds"]
        
        # Prepare Habits (Convert list to dict for consistency with Schema)
        habits_payload = {h: True for h in (request.habits or [])}

        # Robust Metrics Extraction
        metrics = meta_payload.get("metrics")
        if not isinstance(metrics, dict):
            metrics = {}
        
        mood = metrics.get("mood", 5)
        focus = metrics.get("focus", 5)
        energy = metrics.get("energy", 5)

        db_payload = {
            "id": str(uuid.uuid4()),
            "date": request.date,
            "content": ai_data.get("markdown_body", request.text),
            "mood": mood,
            "focus": focus,
            "energy": energy,
            "isAi": not request.skip_ai and (ai_data is not None),
            "aiModel": model_name if not request.skip_ai else "None",
            "tags": ai_data.get("tags", []),
            "habits": habits_payload,
            "meta": meta_payload,
            "updatedAt": datetime.datetime.now().isoformat()
        }
        
        if supabase:
            try:
                # 1. Try Full Insert (New Schema)
                try:
                    res = supabase.table("LogEntry").insert(db_payload).execute()
                    logger.info("✅ Memory stored (New Entry).")
                except Exception as full_insert_error:
                    error_str = str(full_insert_error)
                    
                    # Case A: Column missing (Schema Mismatch)
                    if "column" in error_str and "does not exist" in error_str:
                         logger.warning("⚠️ DB Schema missing v7 columns. Falling back to legacy storage...")
                         # Fallback to legacy payload
                         legacy_payload = {
                             "id": db_payload["id"],
                             "date": db_payload["date"],
                             "content": db_payload["content"],
                             "mood": db_payload["mood"],
                             "focus": db_payload["focus"],
                             "energy": db_payload["energy"]
                         }
                         # Try Legacy Insert
                         try:
                             res = supabase.table("LogEntry").insert(legacy_payload).execute()
                             logger.info("✅ Memory stored (Legacy Entry).")
                         except Exception as legacy_error:
                             # Check for duplicate on legacy insert
                             if "23505" in str(legacy_error) or "duplicate key" in str(legacy_error).lower():
                                 logger.info("⚠️ Duplicate date detected (Legacy). Updating...")
                                 del legacy_payload["id"]
                                 res = supabase.table("LogEntry").update(legacy_payload).eq("date", request.date).execute()
                             else:
                                 raise legacy_error

                    # Case B: Duplicate Key (New Schema)
                    elif "23505" in error_str or "duplicate key" in error_str.lower():
                        logger.info("⚠️ Duplicate date detected. Updating existing entry...")
                        update_payload = {k: v for k, v in db_payload.items() if k != "id"}
                        res = supabase.table("LogEntry").update(update_payload).eq("date", request.date).execute()
                        logger.info("✅ Memory updated (Existing Entry).")
                    
                    # Case C: Other Error
                    else:
                        raise full_insert_error
                        
            except Exception as db_e:
                logger.error(f"❌ Database Write/Update Failed: {db_e}")
                # Swallow error to return AI response

        
        # 4. 回傳給前端
        return {
            "success": True,
            "model": model_name,
            "data": ai_data
        }

    except Exception as e:
        logger.error(f"🔥 Ingest Critical Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))