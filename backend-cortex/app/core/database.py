# 檔案: backend-cortex/app/core/database.py
import os
from supabase import create_client, Client
from app.core.config import settings

# 建立單例模式 (Singleton) 的資料庫連線
# 這相當於您前端的 createClient()
def get_supabase_client() -> Client:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY") # 注意：後端通常使用 SERVICE_ROLE_KEY 以獲得完整寫入權限，或使用 ANON_KEY
    
    if not url or not key:
        raise ValueError("❌ Supabase credentials not found in .env")

    return create_client(url, key)
