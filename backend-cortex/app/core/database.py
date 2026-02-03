# 檔案位置: backend-cortex/app/core/database.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. 確保能讀取到 .env 檔案
load_dotenv()

# 2. 讀取環境變數
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY") 

# 3. 建立連線實例 (Singleton)
if not url or not key:
    print("⚠️  Warning: SUPABASE_URL or SUPABASE_KEY not found in .env")
    # 為了避免 import 報錯導致整個後端崩潰，這裡先給 None，但在 ingest 時會報錯
    supabase = None
else:
    # 這就是 ingest.py 正在尋找的變數 'supabase'
    supabase: Client = create_client(url, key)
