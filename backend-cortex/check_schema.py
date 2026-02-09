import asyncio
import os
from app.core.database import supabase

async def check_schema():
    if not supabase:
        print("No supabase client")
        return

    try:
        # Fetch 1 row to see columns
        res = supabase.table("LogEntry").select("*").limit(1).execute()
        if res.data and len(res.data) > 0:
            print("Columns found:", res.data[0].keys())
        else:
            print("Table empty, cannot infer columns easily, but connection works.")
            # Try to insert a dummy with only base columns to confirm base works
            print("Try inserting dummy...")
            try:
                # Intentionally minimal
                dummy = {
                    "date": "1000-01-01",
                    "content": "Schema Check",
                    "mood": 5, 
                    "focus": 5, 
                    "energy": 5
                }
                supabase.table("LogEntry").insert(dummy).execute()
                print("Base insert success")
                # cleanup
                supabase.table("LogEntry").delete().eq("date", "1000-01-01").execute()
            except Exception as e:
                print("Base insert failed:", e)

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(check_schema())
