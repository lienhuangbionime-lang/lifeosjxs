
import asyncio
import os
from dotenv import load_dotenv
load_dotenv("C:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")
from app.core.database import supabase

async def check_archive():
    print("--- Searching for any chat_auto_archive documents ---")
    if not supabase: return
    
    # Search in metadata
    res = supabase.table("documents").select("id, title, metadata").limit(5).execute()
    found = False
    if res.data:
        for d in res.data:
            meta = d.get('metadata', {})
            if meta.get('source') == "chat_auto_archive" or meta.get('source') == "web_search":
                print(f"Found: [{meta.get('source')}] {d['title']}")
                found = True
    
    if not found:
        print("No archived chat/search documents found in the last 5 entries.")

if __name__ == "__main__":
    asyncio.run(check_archive())
