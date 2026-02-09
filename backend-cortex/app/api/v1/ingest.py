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

@router.post("/ingest") 
async def ingest_log(request: IngestRequest):
    logger.info(f"🧠 Cortex receiving input for {request.date}...")
    
    try:
        # 1. 呼叫 Gemini with v7.1 Prompt
        import google.generativeai as genai
        
        model_config = get_model("smart") 
        if not model_config.get("configured"):
             logger.warning("Gemini API Key not set, using mock response")
        
        # 初始化模型物件
        model_name = model_config.get("model", "gemini-2.0-flash")
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
        
        response = model.generate_content(full_prompt)
        
        # 2. 解析 JSON
        try:
            cleaned_text = response.text.strip()
            # 移除可能的 markdown code block 標記
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
                
            ai_data = json.loads(cleaned_text.strip())
        except Exception as e:
            logger.error(f"JSON Parse Error: {e}")
            logger.error(f"Raw response: {response.text[:500]}")
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
        db_payload = {
            "date": request.date,
            "note": ai_data.get("markdown_body", request.text),
            "mood": ai_data.get("meta", {}).get("metrics", {}).get("mood", 5),
            "focus": ai_data.get("meta", {}).get("metrics", {}).get("focus", 5),
            "energy": ai_data.get("meta", {}).get("metrics", {}).get("energy", 5),
            "is_ai": True,
            "ai_model": model_name,
            "created_at": datetime.datetime.now().isoformat()
        }

        if supabase:
            try:
                data, count = supabase.table("logentry").insert(db_payload).execute()
                logger.info("✅ Memory stored in Hippocampus.")
            except Exception as db_e:
                logger.error(f"❌ Database Write Failed: {db_e}")
        
        # 4. 回傳給前端
        return {
            "success": True,
            "model": model_name,
            "data": ai_data
        }

    except Exception as e:
        logger.error(f"🔥 Ingest Critical Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))