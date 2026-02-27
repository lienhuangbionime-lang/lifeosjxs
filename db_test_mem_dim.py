
import asyncio
import os
from dotenv import load_dotenv
load_dotenv("C:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")
from app.core.database import supabase
from app.services.embedder import generate_embedding

async def test_memories_dim():
    print("--- Testing 'memories' Embedding Dim ---")
    if not supabase: return
    
    text = "Dimension test."
    embedding = await generate_embedding(text) # This is 3072
    
    # Try to insert a dummy memory
    payload = {
        "content": "Dim test internal",
        "date": "2099-01-01",
        "embedding": embedding
    }
    
    try:
        res = supabase.table("memories").insert(payload).execute()
        print("Success! memories accepts 3072.")
        # Cleanup
        supabase.table("memories").delete().eq("date", "2099-01-01").execute()
    except Exception as e:
        print(f"Failed to insert into memories: {e}")

if __name__ == "__main__":
    asyncio.run(test_memories_dim())
