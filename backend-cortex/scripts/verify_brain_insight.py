# [v6.0] Neural Edge Verification: Brain Insight System
import asyncio
import os
import httpx
from dotenv import load_dotenv

# Terminal Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def test_endpoint(client, label):
    print(f"Testing Insight for: '{label}'...")
    try:
        url = f"http://localhost:8000/api/v1/brain/node/{label}/insight"
        # We also need to check the context endpoint to see scoring
        context_url = f"http://localhost:8000/api/v1/brain/node/{label}/context"
        
        # 1. Test Insight Generation
        res = await client.get(url, timeout=20.0)
        if res.status_code != 200:
            return False, f"HTTP {res.status_code}: {res.text}"
        
        data = res.json()
        insight = data.get("insight", "")
        if not insight or "尚無足夠的上下文" in insight:
             return False, "Insight missing or returned 'no context' fallback."
             
        # 2. Test Context Scoring
        ctx_res = await client.get(context_url)
        if ctx_res.status_code == 200:
            memories = ctx_res.json()
            if memories:
                for m in memories:
                    # [v6.0] Standard score check
                    score = m.get("similarity") or m.get("_hybrid_score")
                    if score is None:
                        return False, "Score (similarity/_hybrid_score) missing from memory metadata."
                    
        return True, f"Success! Insight: {insight[:50]}..."
    except Exception as e:
        return False, str(e)

async def main():
    load_dotenv()
    print("=== Neural Edge v7.0: Brain Insight Verification ===")
    
    async with httpx.AsyncClient() as client:
        # TEST 1: Date Exact Match (YYYY-MM-DD)
        # Note: This requires at least one memory in DB or it might still work via cold-start if we allow it.
        # But for dates, it should match specifically.
        ok, msg = await test_endpoint(client, "2025-12-13")
        print(f"Test 1 (Date Match): {'[PASS]' if ok else '[FAIL]'} {msg}")
        
        # TEST 2: Project Cold Start (Mock name)
        # Assuming "LifeOS v4.0" is in the projects table
        ok, msg = await test_endpoint(client, "LifeOS v4.0")
        print(f"Test 2 (Cold Start): {'[PASS]' if ok else '[FAIL]'} {msg}")

        # TEST 3: Hybrid Score Check
        ok, msg = await test_endpoint(client, "LifeOS")
        print(f"Test 3 (Hybrid Score): {'[PASS]' if ok else '[FAIL]'} {msg}")

if __name__ == "__main__":
    asyncio.run(main())
