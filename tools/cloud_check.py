#!/usr/bin/env python3
"""
tools/cloud_check.py — 檢查雲端 Supabase 資料狀態
執行: python tools/cloud_check.py
"""
import os
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "backend-cortex", ".env"))

def main():
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            print("[ERROR] .env 中找不到 SUPABASE_URL 或 SUPABASE_KEY")
            return

        print(f"--- Supabase Cloud Check ---")
        print(f"URL: {url}")
        
        supabase = create_client(url, key)
        
        # 1. Check memories count
        try:
            res = supabase.table("memories").select("id", count="exact").limit(1).execute()
            print(f"[OK] memories 表存在。紀錄筆數: {res.count}")
        except Exception as e:
            print(f"[ERROR] memories 表存取失敗: {e}")

        # 2. Check cortex_growth_logs count
        try:
            res = supabase.table("cortex_growth_logs").select("id", count="exact").limit(1).execute()
            print(f"[OK] cortex_growth_logs 表存在。紀錄筆數: {res.count}")
        except Exception as e:
            print(f"[ERROR] cortex_growth_logs 表存取失敗: {e}")

        # 3. Check nodes/edges
        try:
            res_n = supabase.table("nodes").select("id", count="exact").limit(1).execute()
            res_e = supabase.table("edges").select("id", count="exact").limit(1).execute()
            print(f"[OK] 知識圖譜: {res_n.count} nodes, {res_e.count} edges")
        except Exception as e:
            print(f"[ERROR] 知識圖譜表存取失敗: {e}")

    except ImportError:
        print("[ERROR] 請安裝 supabase 套件: pip install supabase")

if __name__ == "__main__":
    main()
