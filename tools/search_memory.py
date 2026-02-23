#!/usr/bin/env python3
"""
tools/search_memory.py — 開發 AI 語意記憶搜尋
執行: python tools/search_memory.py "embedding model 問題"
     python tools/search_memory.py "focus score" --table growth
"""
import sys
import os
import argparse
import json

# Try to load .env for local API URL
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

def search(query: str, table: str = "growth", limit: int = 5):
    """Call the backend semantic search endpoint."""
    try:
        import urllib.request
        import urllib.parse

        if table == "growth":
            url = f"{API_BASE}/api/v1/brain/growth/search?q={urllib.parse.quote(query)}&limit={limit}"
        else:
            # memories — use hybrid search endpoint
            url = f"{API_BASE}/api/v1/brain/search?q={urllib.parse.quote(query)}&limit={limit}"

        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        print(f"  Make sure backend is running at {API_BASE}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Dev AI Memory Search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--table", choices=["growth", "memories"], default="growth",
                        help="Which table to search (default: growth = cortex_growth_logs)")
    parser.add_argument("--limit", type=int, default=5, help="Number of results")
    args = parser.parse_args()

    print(f"\n[Search] \"{args.query}\" in {args.table} (top {args.limit})\n")

    data = search(args.query, args.table, args.limit)
    results = data.get("results", [])

    if not results:
        print("  No results found.")
        return

    print(f"  Found {data.get('total', len(results))} results:\n")
    for i, r in enumerate(results, 1):
        similarity = r.get("similarity", 0)
        print(f"  [{i}] Similarity: {similarity:.3f}")

        if args.table == "growth":
            print(f"      Context: {r.get('decision_context', '')[:80]}")
            match = r.get("prediction_match")
            match_str = "[OK]" if match else "[MISS]"
            print(f"      {match_str} AI predicted: {r.get('ai_prediction','?')} | Chose: {r.get('user_choice','?')}")
            lessons = r.get("lessons_learned", "")
            if lessons:
                print(f"      Lesson: {lessons[:100]}")
        else:
            print(f"      Content: {r.get('content', '')[:120]}")
            print(f"      Date: {r.get('metadata', {}).get('date', '?')}")
        print()

if __name__ == "__main__":
    main()
