
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
    print("--- Testing LogEntry Insertion V4 (Exact Ingest Payload) ---")
    
    # Exact payload from ingest.py
    model_name = "gemini-2.5-flash-mock"
    request_date = "2099-01-05"
    request_text = "Debug Entry Simulation"
    
    db_payload = {
        "id": str(uuid.uuid4()),
        "date": request_date,
        "content": request_text,
        "mood": 5,
        "focus": 5,
        "energy": 5,
        "isAi": True,
        "aiModel": model_name,
        "updatedAt": datetime.datetime.now().isoformat()
    }
    
    print(f"\nPayload: {db_payload}")
    
    try:
        res = supabase.table("LogEntry").insert(db_payload).execute()
        print("   SUCCESS!", res.data)
        # Cleanup
        supabase.table("LogEntry").delete().eq("date", request_date).execute()
    except Exception as e:
        print("   FAILED:", e)

if __name__ == "__main__":
    asyncio.run(test_log_insert())
