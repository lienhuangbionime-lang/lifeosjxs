
import asyncio
import os
from dotenv import load_dotenv
load_dotenv("C:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")
from app.core.database import supabase

async def deep_check():
    print("--- Checking last 20 entries in 'documents' ---")
    if not supabase: return
    
    res = supabase.table("documents").select("id, title, doc_type, metadata, created_at").order("created_at", desc=True).limit(20).execute()
    if res.data:
        for d in res.data:
            meta = d.get('metadata', {})
            print(f"- [{d['created_at']}] [{d['doc_type']}] {d['title']} (Source: {meta.get('source')})")
    else:
        print("Documents table is empty.")

    print("\n--- Checking for 'lm.pl' or 'Agent Skills' ---")
    res_search = supabase.table("documents").select("id, title, content").ilike("content", "%lm.pl%").execute()
    if res_search.data:
        print(f"Found {len(res_search.data)} matches for 'lm.pl'")
    else:
        print("No matches for 'lm.pl'")

    res_skills = supabase.table("documents").select("id, title, content").ilike("title", "%Agent Skills%").execute()
    if res_skills.data:
        print(f"Found {len(res_skills.data)} matches for 'Agent Skills' in title")
    else:
        print("No matches for 'Agent Skills' in title")

if __name__ == "__main__":
    asyncio.run(deep_check())
