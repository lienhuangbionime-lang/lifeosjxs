# [v7.1] Brain Logic Diagnostic (Neural Edge Optimized)
import os
import asyncio
from dotenv import load_dotenv

# Step 1: Force Load Environment
load_dotenv("c:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")
# No hardcoded fallbacks in v7.1!

import app.core.gemini as gemini_core
# Force re-initialization of global key if it was None during import
gemini_core.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_core.gemini_client = gemini_core.get_gemini_client()

from fastapi import Request
from unittest.mock import MagicMock
from app.api.v1.brain import get_node_insight

async def diagnose(label="2025-12-13"):
    print(f"=== Neural Edge v7.1: Final Integration Test [{label}] ===")
    
    # Check Dependency
    try:
        from sentence_transformers import CrossEncoder
        print("[OK] sentence_transformers is IMPORTABLE.")
    except ImportError:
        print("[FAIL] sentence_transformers is MISSING.")
    
    # Check Gemini
    if gemini_core.gemini_client:
        print("[OK] Gemini Client Initialized.")
    else:
        print("[FAIL] Gemini Client Missing.")
    
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    
    print(f"Executing get_node_insight('{label}')...")
    try:
        result = await get_node_insight(mock_request, label)
        print(f"Result (truncated): {str(result)[:200]}...")
        
        insight = result.get("insight", "")
        if insight and "無法產生" not in insight:
            print(">>> VERIFICATION SUCCESS: All systems nominal.")
        else:
            print(">>> VERIFICATION WARNING: Sparse or failed insight.")
            
    except Exception as e:
        print(f"CRITICAL CRASH: {e}")

if __name__ == "__main__":
    import sys
    label = sys.argv[1] if len(sys.argv) > 1 else "LifeOS"
    asyncio.run(diagnose(label))
