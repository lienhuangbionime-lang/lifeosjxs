# 檔案位置: backend-cortex/app/api/v1/memories.py

from fastapi import APIRouter, HTTPException
from app.core.database import supabase  # 這是我們之前建立的資料庫連線

router = APIRouter()

# 這行代表：當有人訪問 "網址/memories/daily" 時，執行下面的動作
@router.get("/memories/daily")
async def get_daily_memories(limit: int = 30):
    """
    這段函式是去 Supabase (海馬迴) 把日記拿出來
    """
    try:
        # 1. table("logs"): 打開叫做 logs 的資料表
        # 2. select("*"): 拿出所有欄位 (mood, content, date...)
        # 3. order("date", desc=True): 按照日期「降序」排 (最新的在最上面)
        # 4. limit(limit): 只拿前 30 筆 (避免一次拿太多跑不動)
        response = supabase.table("logs")\
            .select("*")\
            .order("date", desc=True)\
            .limit(limit)\
            .execute()
            
        # 把拿到的資料 (response.data) 直接回傳給前端
        return response.data

    except Exception as e:
        # 如果出錯 (例如資料庫連不上)，告訴前端發生什麼事
        raise HTTPException(status_code=500, detail=f"Recall Error: {str(e)}")