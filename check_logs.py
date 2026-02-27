
import asyncio
import os
from dotenv import load_dotenv
load_dotenv("C:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")
from app.core.database import supabase

async def check_logs():
    print("--- Checking 'cortex_growth_logs' for today ---")
    if not supabase: return
    
    from app.core.time_utils import get_today_str_taipei
    today = get_today_str_taipei()
    
    res = supabase.table("cortex_growth_logs").select("*").gte("created_at", today).execute()
    if res.data:
        print(f"Found {len(res.data)} growth logs:")
        for l in res.data:
            print(f"- {l.get('decision_context')[:100]}...")
    else:
        print("No growth logs found for today.")

if __name__ == "__main__":
    asyncio.run(check_logs())
