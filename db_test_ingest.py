
import asyncio
import os
from dotenv import load_dotenv
load_dotenv("C:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")
from app.core.database import supabase
from app.services.embedder import generate_embedding

async def test_ingest():
    print("--- Testing Manual Ingestion into 'documents' (3072 Dim Alignment) ---")
    if not supabase: return
    
    text = "Architecture Aligned: Testing 3072 dimensional ingestion."
    # Back to 3072
    embedding = await generate_embedding(text, dimensionality=3072)
    
    payload = {
        "content": text,
        "title": "Test Ingestion",
        "metadata": {"source": "debug_script"},
        "embedding": embedding,
        "doc_type": "note"
    }
    
    try:
        res = supabase.table("documents").insert(payload).execute()
        print("Success! Data inserted.")
        print(f"Result: {res.data}")
    except Exception as e:
        print(f"Failed to insert: {e}")

if __name__ == "__main__":
    asyncio.run(test_ingest())
