# 檔案: backend-cortex/app/core/database.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 載入 .env 環境變數
load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

# 防禦性編程：如果沒有 Key，不要讓整個後端崩潰，而是設為 None
if not url or not key:
    print("⚠️  Warning: Supabase credentials missing via os.getenv")
    supabase = None
else:
    try:
        supabase: Client = create_client(url, key)
    except Exception as e:
        print(f"⚠️  Supabase Connection Error: {e}")
        supabase = None