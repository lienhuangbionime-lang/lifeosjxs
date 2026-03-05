
import asyncio
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

from app.api.v1.ingest import ingest_log, IngestRequest
from fastapi import BackgroundTasks
from unittest.mock import MagicMock

async def test_ingest():
    print("Testing Ingest with Task Extraction...")
    
    # Mocking Request/BackgroundTasks
    mock_request = MagicMock()
    mock_request.state.gemini_client = None # Will use default
    mock_request.state.supabase_client = None # Will use default
    
    bg_tasks = BackgroundTasks()
    
    sample_content = """
# 2026-03-06 專案進度
今天研發了影片專案，決定要有三個步驟：
1. 建立腳本範本
2. 匯入服飾圖片
3. 測試語音合成
- Mood: 8
- Focus: 9
- Energy: 8
"""
    
    req = IngestRequest(
        content=sample_content,
        source="web_terminal",
        date="2026-03-06"
    )
    
    # We call the handler directly
    # Note: ingest_log handles DB writes inside
    result = await ingest_log(mock_request, req, bg_tasks)
    
    print("\nResult Data:")
    print(json.dumps(result.get("data", {}), indent=2, ensure_ascii=False))
    
    tasks = result.get("data", {}).get("tasks", [])
    if tasks:
        print(f"\nSUCCESS: Extracted {len(tasks)} tasks.")
        for t in tasks:
            print(f"- {t.get('title')}")
    else:
        print("\nFAILED: No tasks extracted.")

if __name__ == "__main__":
    asyncio.run(test_ingest())
