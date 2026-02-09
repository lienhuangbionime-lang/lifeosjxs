
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client
import uuid
import datetime

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

async def test_log_insert():
    print("--- Testing LogEntry Insertion V3 ---")
    
    # Payload WITHOUT created_at (to rely on Default)
    print("\n1. Trying WITHOUT any timestamp column...")
    db_payload = {
        "id": str(uuid.uuid4()),
        "date": "2099-01-03", 
        "content": "Debug Entry No Timestamp",
        "mood": 5,
        "isAi": True,
        "aiModel": "gemini-2.5-flash"
    }
    try:
        res = supabase.table("LogEntry").insert(db_payload).execute()
        print("   SUCCESS! (DB Defaults used)", res.data)
        supabase.table("LogEntry").delete().eq("date", "2099-01-03").execute()
    except Exception as e:
        print("   FAILED:", e)

    # Payload WITH createdAt (camelCase)
    print("\n2. Trying WITH 'createdAt'...")
    db_payload_2 = {
        "id": str(uuid.uuid4()),
        "date": "2099-01-04", 
        "content": "Debug Entry createdAt",
        "mood": 5,
        "isAi": True,
        "createdAt": datetime.datetime.now().isoformat()
    }
    try:
        res = supabase.table("LogEntry").insert(db_payload_2).execute()
        print("   SUCCESS! (createdAt accepted)", res.data)
        supabase.table("LogEntry").delete().eq("date", "2099-01-04").execute()
    except Exception as e:
        print("   FAILED:", e)

if __name__ == "__main__":
    asyncio.run(test_log_insert())
