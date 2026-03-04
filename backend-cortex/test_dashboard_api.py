import asyncio
import os
import httpx

async def test_endpoints():
    url = "http://127.0.0.1:8000"
    
    # We will pretend to be the frontend, with no headers, to see what happens
    async with httpx.AsyncClient() as client:
        print("--- NO HEADERS (Guest Mode) ---")
        try:
            r1 = await client.get(f"{url}/api/v1/memories?limit=1")
            print("Memories:", r1.status_code, r1.text[:100])
        except Exception as e: print("Err1:", e)
        
        try:
            r2 = await client.get(f"{url}/api/v1/tasks")
            print("Tasks:", r2.status_code, r2.text[:100])
        except Exception as e: print("Err2:", e)
        
        try:
            r3 = await client.get(f"{url}/api/v1/projects")
            print("Projects:", r3.status_code, r3.text[:100])
        except Exception as e: print("Err3:", e)

    # Now with system headers (Simulator of Owner Mode IF we know the keys)
    from dotenv import load_dotenv
    load_dotenv("c:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")
    
    headers = {
        "X-Supabase-URL": os.environ.get("SUPABASE_URL", ""),
        "X-Supabase-Key": os.environ.get("SUPABASE_KEY", ""),
        "X-Gemini-Key": os.environ.get("GEMINI_API_KEY", "")
    }
    
    async with httpx.AsyncClient(headers=headers) as client:
        print("\n--- WITH ENV VAR HEADERS (Owner Mode Simulator) ---")
        try:
            r1 = await client.get(f"{url}/api/v1/memories?limit=1")
            print("Memories:", r1.status_code, r1.text[:100])
        except Exception as e: print("Err1:", e)
        
        try:
            r2 = await client.get(f"{url}/api/v1/tasks")
            print("Tasks:", r2.status_code, r2.text[:100])
        except Exception as e: print("Err2:", e)
        
        try:
            r3 = await client.get(f"{url}/api/v1/projects")
            print("Projects:", r3.status_code, r3.text[:100])
        except Exception as e: print("Err3:", e)

if __name__ == "__main__":
    asyncio.run(test_endpoints())
