"""
LifeOS v3.1 - Dual-Write Ingest API
雙寫入策略：同時寫入 Supabase 和 C Kernel

設計理念：
- Supabase: 工作副本（可編輯、可搜尋、給前端用）
- C Kernel: 數位原版（不可變、永久保存、給自己留底）
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import sys
from pathlib import Path

# 添加 backend-cortex 到 Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from kernel_driver import LifeKernel


router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])

# 初始化 C Kernel
try:
    kernel = LifeKernel(auto_compile=True)
    print("✅ C Kernel initialized successfully")
except Exception as e:
    print(f"⚠️ C Kernel initialization failed: {e}")
    print("⚠️ Will continue with Supabase only")
    kernel = None


# ============================================================================
# Pydantic Models
# ============================================================================

class LogEntry(BaseModel):
    """日記條目"""
    content: str = Field(..., description="日記內容")
    mood: int = Field(..., ge=0, le=10, description="心情 (0-10)")
    focus: int = Field(..., ge=0, le=10, description="專注度 (0-10)")
    energy: int = Field(..., ge=0, le=10, description="能量 (0-10)")
    date: Optional[str] = Field(None, description="日期 (YYYY-MM-DD)，不提供則為今天")


class IngestResponse(BaseModel):
    """寫入回應"""
    status: str
    db_id: Optional[str] = None
    kernel_locked: bool
    kernel_day_offset: Optional[int] = None
    message: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/log", response_model=IngestResponse)
async def ingest_log(entry: LogEntry):
    """
    寫入日記（雙寫入策略）
    
    流程：
    1. 寫入 Supabase (雲端 / 可變動層) -> 給前端看
    2. 寫入 C Kernel (本地 / 不可變層) -> 給自己留底
    
    Args:
        entry: 日記條目
    
    Returns:
        寫入結果
    """
    try:
        # 解析日期
        if entry.date:
            log_date = datetime.strptime(entry.date, "%Y-%m-%d")
        else:
            log_date = datetime.now()
        
        # ========================================
        # 1. 寫入 Supabase (工作副本)
        # ========================================
        try:
            from supabase import create_client
            import os
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                
                data = {
                    "date": log_date.date().isoformat(),
                    "content": entry.content,
                    "mood": entry.mood,
                    "focus": entry.focus,
                    "energy": entry.energy,
                    "created_at": datetime.now().isoformat()
                }
                
                db_result = supabase.table("memories").insert(data).execute()
                db_id = db_result.data[0]['id'] if db_result.data else None
                print(f"✅ Supabase: Saved to DB (ID: {db_id})")
            else:
                db_id = None
                print("⚠️ Supabase: Not configured, skipping")
        
        except Exception as e:
            print(f"⚠️ Supabase write failed: {e}")
            db_id = None
        
        # ========================================
        # 2. 寫入 C Kernel (數位原版)
        # ========================================
        kernel_locked = False
        kernel_day_offset = None
        
        if kernel:
            try:
                kernel_locked = kernel.save(
                    date=log_date,
                    content=entry.content,
                    mood=entry.mood,
                    focus=entry.focus,
                    energy=entry.energy
                )
                kernel_day_offset = kernel.get_day_offset(log_date)
                
                if kernel_locked:
                    print(f"✅ C Kernel: Locked (Day {kernel_day_offset})")
                else:
                    print(f"⚠️ C Kernel: Already exists (Day {kernel_day_offset})")
            
            except Exception as e:
                print(f"❌ C Kernel write failed: {e}")
        
        # ========================================
        # 3. 返回結果
        # ========================================
        if db_id and kernel_locked:
            status = "synced"
            message = "Successfully synced to both Supabase and C Kernel"
        elif db_id:
            status = "db_only"
            message = "Saved to Supabase only (Kernel already exists or unavailable)"
        elif kernel_locked:
            status = "kernel_only"
            message = "Saved to C Kernel only (Supabase unavailable)"
        else:
            status = "failed"
            message = "Failed to save to both systems"
        
        return IngestResponse(
            status=status,
            db_id=db_id,
            kernel_locked=kernel_locked,
            kernel_day_offset=kernel_day_offset,
            message=message
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/{date}")
async def verify_entry(date: str):
    """
    驗證指定日期的記錄
    
    檢查：
    - Supabase 中是否存在
    - C Kernel 中是否存在
    - 兩者內容是否一致
    
    Args:
        date: YYYY-MM-DD
    
    Returns:
        驗證結果
    """
    try:
        log_date = datetime.strptime(date, "%Y-%m-%d")
        
        # 從 Supabase 讀取
        db_content = None
        try:
            from supabase import create_client
            import os
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                result = supabase.table("memories").select("*").eq("date", date).execute()
                
                if result.data:
                    db_content = result.data[0]['content']
        except Exception as e:
            print(f"⚠️ Supabase read failed: {e}")
        
        # 從 C Kernel 讀取
        kernel_content = None
        if kernel:
            try:
                result = kernel.read(log_date)
                if result:
                    marker, text = result
                    kernel_content = text
            except Exception as e:
                print(f"⚠️ C Kernel read failed: {e}")
        
        # 比較
        exists_in_db = db_content is not None
        exists_in_kernel = kernel_content is not None
        content_match = db_content == kernel_content if (exists_in_db and exists_in_kernel) else None
        
        return {
            "date": date,
            "exists_in_db": exists_in_db,
            "exists_in_kernel": exists_in_kernel,
            "content_match": content_match,
            "db_length": len(db_content) if db_content else 0,
            "kernel_length": len(kernel_content) if kernel_content else 0,
            "status": "verified" if content_match else "mismatch" if (exists_in_db and exists_in_kernel) else "partial"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kernel/read/{date}")
async def read_from_kernel(date: str):
    """
    直接從 C Kernel 讀取（用於驗證數位原版）
    
    Args:
        date: YYYY-MM-DD
    
    Returns:
        C Kernel 中的原始記錄
    """
    if not kernel:
        raise HTTPException(status_code=503, detail="C Kernel not available")
    
    try:
        log_date = datetime.strptime(date, "%Y-%m-%d")
        result = kernel.read(log_date)
        
        if not result:
            raise HTTPException(status_code=404, detail="Entry not found in C Kernel")
        
        marker, text = result
        
        return {
            "date": date,
            "day_offset": kernel.get_day_offset(log_date),
            "content": text,
            "metrics": {
                "mood": marker.mood,
                "focus": marker.focus,
                "energy": marker.energy
            },
            "metadata": {
                "text_offset": marker.text_offset,
                "text_len": marker.text_len,
                "created_at": datetime.fromtimestamp(marker.created_at).isoformat(),
                "word_count": marker.word_count,
                "media_count": marker.media_count
            },
            "source": "C Kernel (Digital Original)"
        }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kernel/status")
async def kernel_status():
    """
    獲取 C Kernel 狀態
    
    Returns:
        Kernel 狀態信息
    """
    from pathlib import Path
    
    idx_path = Path("backend-cortex/kernel/storage/life.index")
    txt_path = Path("backend-cortex/kernel/storage/life.text")
    
    return {
        "kernel_available": kernel is not None,
        "index_file_exists": idx_path.exists(),
        "text_file_exists": txt_path.exists(),
        "index_file_size": idx_path.stat().st_size if idx_path.exists() else 0,
        "text_file_size": txt_path.stat().st_size if txt_path.exists() else 0,
        "estimated_entries": idx_path.stat().st_size // 32 if idx_path.exists() else 0,
        "storage_path": str(idx_path.parent) if idx_path.exists() else None
    }
