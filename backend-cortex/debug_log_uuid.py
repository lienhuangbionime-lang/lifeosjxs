
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
    print("--- Testing LogEntry Insertion V2 ---")
    
    # Simulate the payload used in ingest.py
    db_payload = {
        "id": str(uuid.uuid4()),
        "date": "2099-01-02", # different date
        "content": "Debug Entry UUID Test",
        "mood": 5,
        "focus": 5,
        "energy": 5,
        "isAi": True,
        "aiModel": "gemini-2.5-flash", 
        "created_at": datetime.datetime.now().isoformat()
    }
    
    print(f"\nPayload: {db_payload}")
    print("\nTrying insert into 'LogEntry'...")
    try:
        res = supabase.table("LogEntry").insert(db_payload).execute()
        print("   SUCCESS!", res.data)
        # Cleanup
        supabase.table("LogEntry").delete().eq("date", "2099-01-02").execute()
    except Exception as e:
        print("   FAILED:", e)

if __name__ == "__main__":
    asyncio.run(test_log_insert())
