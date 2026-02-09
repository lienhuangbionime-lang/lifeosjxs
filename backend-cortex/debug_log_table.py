
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

async def test_log_insert():
    print("--- Testing LogEntry Insertion ---")
    data = {
        "date": "2099-01-01",
        "content" : "Debug Entry",  # Note: schema might be 'content' or 'note'
        "mood": 5,
        "isAi": True
    }
    
    # Try 'LogEntry' with 'content'
    print("\n1. Trying 'LogEntry' with field 'content'...")
    try:
        res = supabase.table("LogEntry").insert(data).execute()
        print("   SUCCESS!", res.data)
        supabase.table("LogEntry").delete().eq("date", "2099-01-01").execute()
        return
    except Exception as e:
        print("   FAILED:", e)

    # Try 'LogEntry' with 'note' (as used in ingest.py currently)
    print("\n2. Trying 'LogEntry' with field 'note'...")
    try:
        data["note"] = data.pop("content")
        res = supabase.table("LogEntry").insert(data).execute()
        print("   SUCCESS!", res.data)
        supabase.table("LogEntry").delete().eq("date", "2099-01-01").execute()
        return
    except Exception as e:
        print("   FAILED:", e)

    # Try lowercase 'logentry'
    print("\n3. Trying 'logentry'...")
    try:
        res = supabase.table("logentry").insert(data).execute()
        print("   SUCCESS!", res.data)
    except Exception as e:
        print("   FAILED:", e)

if __name__ == "__main__":
    asyncio.run(test_log_insert())
