# [v6.0] RAG Diagnostic Tool
import asyncio
import os
from supabase import create_client
from dotenv import load_dotenv

async def diagnose(query="LifeOS v4.0"):
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    print(f"Testing RAG recall for: '{query}'")
    
    # 1. Test Keyword Search fallback (simulating brain.py logic)
    res = supabase.table("memories").select("id, date, content, tags").or_(f"content.ilike.%{query}%,ai_insights.ilike.%{query}%").limit(5).execute()
    print(f"\n[Keyword Match]: Found {len(res.data or [])} results")
    for m in (res.data or []):
        if not m: continue
        d = m.get('date', 'Unknown')
        c = m.get('content', 'No Content') or 'No Content'
        print(f"  - [{d}] {c[:100]}...")

    # 2. Test Vector Search (RPC match_memories)
    # This requires an embedding for the query.
    # We'll use the Gemini embedding if available or just check if the RPC works.
    print(f"\n[Vector Search]: Attempting to fetch embeddings for '{query}'...")
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        emb_res = client.models.embed_content(model="text-embedding-004", contents=query)
        embedding = emb_res.embeddings[0].values
        
        rpc_res = supabase.rpc("match_memories", {
            "query_embedding": embedding,
            "match_threshold": 0.3, # Low threshold for diagnostic
            "match_count": 10
        }).execute()
        
        print(f"  - Vector Found: {len(rpc_res.data or [])} results")
        for m in (rpc_res.data or []):
            print(f"    - [{m['date']}] Score: {m.get('similarity', 0.0):.4f} | {m['content'][:60]}...")
            
    except Exception as e:
        print(f"  - Vector Search Failed: {e}")

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "LifeOS v4.0"
    asyncio.run(diagnose(q))
