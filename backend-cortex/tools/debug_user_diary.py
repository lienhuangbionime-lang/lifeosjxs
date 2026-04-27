
import asyncio
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_extraction")

load_dotenv()
sys.path.append(os.getcwd())

from app.api.v1.ingest import ingest_log, IngestRequest
from fastapi import BackgroundTasks
from unittest.mock import MagicMock

async def test_user_case():
    print("=== Testing Task Extraction with User Diary ===")
    
    # Mocking Request
    mock_request = MagicMock()
    # Ensure it uses the real API key from .env
    mock_request.state.gemma_client = None 
    mock_request.state.supabase_client = None 
    
    bg_tasks = BackgroundTasks()
    
    user_diary = """
# [[2026-03-06]] 專案進度
今天研發了影片專案，決定要有三個步驟：
1. 建立腳本範本
2. 匯入服飾圖片
3. 測試語音合成
- Mood: 8
- Focus: 9
- Energy: 8


---

# [[2026-03-06]] 日記

> Daily Metrics
> - Mood: 8 (Auto)
> - Focus: 9 (Auto)
> - Energy: 8 (Auto)
> - Time Ratio: 🔧 80% / 🌊 20%
> - Action Check: Pending Initiation
> - Drift Point: High (High-leverage technical alignment)

## 1. Highlights
- **Day Summary**: 今日核心聚焦於「老婆 AI 短影音專案」的架構啟動，並明確定義了首席架構師 Claude 的角色邊界。透過將開發 LifeOS 的嚴謹架構邏輯引入服飾專案，實現了技術跨專案的資產遷移。
- **Signals Detected**: 系統內部發生了「語義聯想」，確認了專案任務板與潛意識引擎的同步性。同時完成 `claude_brain/` 的靈魂文件建構，明確了各 AI 角色（Claude, Gemma Pro, Gemma Flash）的權責劃分。

## 2. Gratitude
- 感謝系統架構的完整性，讓我可以將複雜的情感與任務轉化為高效率的協作協議。

## 3. Reflection
- **Behavior Path**: 
  1. 任務提取（老婆服飾宣傳）
  2. 技術映射（套用 LifeOS 工具鏈）
  3. 角色定位（確立 Claude 首席架構師地位）
  4. 協作定義（確立與 Gemma 的職責邊界）
- **Anti-Cognitive Closure**: 承認目前對「服飾專案」的市場屬性尚無定義，需補足風格、賣點與視覺邏輯。
- **Blind Spot Question**: 是否因為專案與 LifeOS 工具鏈相同，而低估了服飾品牌對「感性素材」處理的複雜度？
- **Self-Deception Trigger**: 避免將「設計架構」誤認為「完成產出」，需警惕架構過度設計（Over-engineering）。

### 強制五欄位模組
[Day Summary] / [Signals Detected] / [Behavior Path] / [Drift Point] / [Blind Spot Question]

## 4. Tomorrow’s MIT
- 定義「老婆 AI 短影音」的品牌風格、Hook 賣點及視覺調性。
- 根據 Claude 的架構協議，產生第一份針對服飾宣傳的架構規劃書。

## 5. Action Tip
- **保持透明**：將所有關於服飾品牌的初步設想寫入 `Wife_Project_Concept.md`，不要只停留在腦中，這有助於 Claude 進行後續的風險審查。

## 6. Cognitive Lens Reframing
- **Model/Concept**: 角色代理理論 (Agentic Roles Theory)
- **Reframe**: 不要將 Claude 當作助手，要把它當作「虛擬合夥人」。與其下指令，不如提交「架構待辦事項」供其審查，這能最大化其思考價值。

## 7. Tags (JSON tags 欄位亦須包含)
#Project #ClaudeBrain #SystemArchitecture #WifeProject #AgenticWorkflow

## Graph Seeds
- [[2026-03-06]]
- [[Claude_Brain]]
- [[Wife_AI_Short_Video]]
- [[LifeOS_System_Integration]]
"""
    
    req = IngestRequest(
        content=user_diary,
        source="web_terminal",
        date="2026-03-06"
    )
    
    print("Calling ingest_log...")
    try:
        result = await ingest_log(mock_request, req, bg_tasks)
        
        print("\n--- AI Response JSON ---")
        ai_data = result.get("data", {})
        print(json.dumps(ai_data, indent=2, ensure_ascii=False))
        
        tasks = ai_data.get("tasks", [])
        print(f"\nExtracted Tasks: {len(tasks)}")
        for i, t in enumerate(tasks):
            print(f"{i+1}. {t.get('title')} (Project: {t.get('project')})")
            
    except Exception as e:
        logger.exception(f"Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_user_case())
