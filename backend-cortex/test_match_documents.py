import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("c:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

async def run_test():
    try:
        # Generate dummy vector
        import sys
        sys.path.append("c:/Users/lien.huang/AppData/lifeosjxs/backend-cortex")
        from app.services.embedder import generate_embedding
        vec = await generate_embedding("測試文件區的紀錄", task_type="retrieval_query")
        
        # Test RPC
        if vec:
            res = supabase.rpc("match_documents", {
                "query_embedding": vec,
                "match_threshold": 0.0,
                "match_count": 5
            }).execute()
            print("Documents found:", res.data)
        else:
            print("Embedding failed")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(run_test())
