import asyncio
import logging
import sys
import os

# Context setup to allow importing from app
sys.path.append(os.getcwd())

from app.services.search import search_web, format_search_results

async def test_search():
    logging.basicConfig(level=logging.INFO)
    print("[TEST] Starting LifeOS Web Search Verification...")
    
    query = "AI Reranker 2026 新進展"
    print(f"[TEST] Searching for: '{query}'")
    
    results = await search_web(query, limit=3)
    
    if results:
        print(f"[SUCCESS] Found {len(results)} results.")
        formatted = format_search_results(results)
        print("\n--- Formatted Output ---")
        print(formatted)
        print("------------------------")
    else:
        print("❌ [FAILED] No results found or search error occurred.")

if __name__ == "__main__":
    asyncio.run(test_search())
