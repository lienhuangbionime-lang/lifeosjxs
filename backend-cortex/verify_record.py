import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("Fetching inserted record...")
res = supabase.table("memories").select("id, content, date, embedding").eq("id", "0080eb88-e9d6-495e-9375-3cadd191a6db").execute()
if res.data:
    record = res.data[0]
    print(f"ID: {record['id']}")
    print(f"Date: {record['date']}")
    emb = record.get('embedding')
    if emb:
        # embedding might be a string like "[0.1, ...]" or a list
        if isinstance(emb, str):
            import json
            emb = json.loads(emb)
        print(f"Embedding Dimension: {len(emb)}")
    else:
        print("No embedding found.")
else:
    print("Record not found.")
