
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load env before importing app modules
load_dotenv("C:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")

from app.core.database import supabase

async def check_documents():
    print("--- Checking 'documents' table for today ---")
    if not supabase:
        print("Supabase not configured.")
        return

    try:
        from app.core.time_utils import get_today_str_taipei
        today = get_today_str_taipei()
        
        # Check documents schema: using doc_type instead of source
        res = supabase.table("documents").select("id, title, doc_type, metadata, created_at").gte("created_at", today).execute()
        
        if res.data:
            print(f"Found {len(res.data)} documents created today ({today}):")
            for d in res.data:
                source = d.get('metadata', {}).get('source', 'unknown')
                print(f"- [{d['doc_type']}] {d['title']} (Source: {source}) ({d['created_at']})")
        else:
            print(f"No documents found for today ({today}).")
            
        print("\n--- Checking 'memories' table for today ---")
        res_mem = supabase.table("memories").select("id, content, date, created_at").eq("date", today).execute()
        if res_mem.data:
            print(f"Found {len(res_mem.data)} memories for date {today}:")
            for m in res_mem.data:
                content_preview = m['content'][:50].replace('\n', ' ')
                print(f"- {content_preview}... ({m['created_at']})")
        else:
            print(f"No memories found for date {today}.")

    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    asyncio.run(check_documents())
