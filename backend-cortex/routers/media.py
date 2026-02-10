"""
LifeOS Media Core - FastAPI Integration
將 Media Core 整合到 FastAPI 後端

使用方式：
1. 在 main.py 中 import 這個 router
2. app.include_router(media_router)
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from media_core import (
    MediaRef, DiaryMarker, LocationRef, BiometricRef,
    MediaType, StorageClass, MediaChain
)


router = APIRouter(prefix="/api/v1/media", tags=["media"])


# ============================================================================
# Pydantic Models (API Request/Response)
# ============================================================================

class MediaRefResponse(BaseModel):
    """媒體參考 API 回應"""
    content_hash: UUID
    media_type: str
    storage_class: str
    duration_sec: int
    file_size_kb: int
    timestamp: datetime
    storage_path: str
    url: str  # 完整的 URL
    
    # 圖片/影片專用
    width: Optional[int] = None
    height: Optional[int] = None
    
    class Config:
        from_attributes = True


class DiaryWithMedia(BaseModel):
    """日記 + 媒體的完整回應"""
    date: datetime
    text: str
    metrics: dict  # {mood, focus, energy}
    media: List[MediaRefResponse]
    location: Optional[dict] = None
    biometrics: Optional[dict] = None


class UploadMediaRequest(BaseModel):
    """上傳媒體的請求"""
    media_type: str = Field(..., description="audio/video/image")
    date: str = Field(..., description="YYYY-MM-DD")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    media_type: str = "image",
    date: str = datetime.now().strftime("%Y-%m-%d")
) -> dict:
    """
    上傳媒體檔案
    
    流程：
    1. 接收檔案
    2. 生成 UUID
    3. 儲存到本機或 S3
    4. 創建 MediaRef
    5. 返回 URL
    """
    try:
        # 讀取檔案
        content = await file.read()
        file_size_kb = len(content) // 1024
        
        # 創建 MediaRef
        from uuid import uuid4
        media = MediaRef(
            content_hash=uuid4(),
            media_type=MediaType[media_type.upper()],
            storage_class=StorageClass.LOCAL,
            duration_sec=0,  # TODO: 從檔案提取
            file_size_kb=file_size_kb,
            storage_path=f"{date.replace('-', '/')}/"
        )
        
        # TODO: 實際儲存檔案到本機或 S3
        # storage_path = save_file(content, media.content_hash)
        
        return {
            "status": "success",
            "data": {
                "content_hash": str(media.content_hash),
                "url": f"/media/{date}/{media.content_hash}.{file.filename.split('.')[-1]}",
                "size_kb": file_size_kb
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diary/{date}")
async def get_diary_with_media(date: str) -> DiaryWithMedia:
    """
    獲取指定日期的日記 + 所有媒體
    
    Args:
        date: YYYY-MM-DD
    
    Returns:
        完整的日記資料（文字 + 媒體 + 位置 + 生物識別）
    """
    try:
        # TODO: 從資料庫讀取 DiaryMarker
        # diary_marker = load_diary_marker(date)
        
        # TODO: 讀取文字內容
        # text = load_text_content(diary_marker.text_offset, diary_marker.text_len)
        
        # TODO: 讀取媒體鏈
        # chain = MediaChain()
        # media_list = chain.get_chain(diary_marker.media_head_ptr)
        
        # 範例回應
        return DiaryWithMedia(
            date=datetime.strptime(date, "%Y-%m-%d"),
            text="今天完成了 Media Core 的 Python 實現...",
            metrics={
                "mood": 8,
                "focus": 9,
                "energy": 7
            },
            media=[
                MediaRefResponse(
                    content_hash=UUID("550e8400-e29b-41d4-a716-446655440000"),
                    media_type="audio",
                    storage_class="local",
                    duration_sec=120,
                    file_size_kb=1024,
                    timestamp=datetime.now(),
                    storage_path="2026/02/10/",
                    url="/media/2026/02/10/audio_001.m4a"
                )
            ],
            location={
                "city": "Taipei",
                "country": "Taiwan",
                "lat": 25.0330,
                "lng": 121.5654
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline")
async def get_timeline(
    start_date: str,
    end_date: str,
    limit: int = 30
) -> List[DiaryWithMedia]:
    """
    獲取時間軸（多天的日記）
    
    Args:
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
        limit: 最多返回幾筆
    
    Returns:
        日記列表
    """
    try:
        # TODO: 從資料庫查詢日期範圍內的所有 DiaryMarker
        # markers = query_diary_markers(start_date, end_date, limit)
        
        # TODO: 對每個 marker 讀取完整資料
        # result = [load_full_diary(marker) for marker in markers]
        
        return []
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/media/{content_hash}")
async def delete_media(content_hash: UUID) -> dict:
    """
    刪除媒體
    
    Args:
        content_hash: 媒體的 UUID
    
    Returns:
        刪除結果
    """
    try:
        # TODO: 從媒體鏈中移除
        # chain = MediaChain()
        # success = chain.remove_media(content_hash)
        
        # TODO: 刪除實際檔案
        # delete_file(content_hash)
        
        return {
            "status": "success",
            "message": f"Media {content_hash} deleted"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Helper Functions
# ============================================================================

def construct_media_url(media: MediaRef) -> str:
    """
    根據 storage_class 構建完整的 URL
    
    Args:
        media: MediaRef
    
    Returns:
        完整的 URL
    """
    if media.storage_class == StorageClass.LOCAL:
        return f"/media/{media.storage_path}{media.content_hash}"
    elif media.storage_class == StorageClass.S3:
        return f"https://s3.amazonaws.com/lifeos/{media.storage_path}{media.content_hash}"
    elif media.storage_class == StorageClass.IPFS:
        return f"ipfs://{media.content_hash}"
    else:
        return f"/media/{media.content_hash}"


def media_ref_to_response(media: MediaRef) -> MediaRefResponse:
    """
    將 MediaRef 轉換為 API 回應格式
    
    Args:
        media: MediaRef
    
    Returns:
        MediaRefResponse
    """
    return MediaRefResponse(
        content_hash=media.content_hash,
        media_type=media.media_type.name.lower(),
        storage_class=media.storage_class.name.lower(),
        duration_sec=media.duration_sec,
        file_size_kb=media.file_size_kb,
        timestamp=media.timestamp,
        storage_path=media.storage_path,
        url=construct_media_url(media),
        width=media.width if media.width > 0 else None,
        height=media.height if media.height > 0 else None
    )


# ============================================================================
# Storage Integration (TODO)
# ============================================================================

async def save_to_local(content: bytes, content_hash: UUID, path: str) -> str:
    """儲存到本機"""
    # TODO: 實現本機儲存
    pass


async def save_to_s3(content: bytes, content_hash: UUID, path: str) -> str:
    """儲存到 S3"""
    # TODO: 實現 S3 上傳
    pass


async def save_to_ipfs(content: bytes) -> str:
    """儲存到 IPFS"""
    # TODO: 實現 IPFS 上傳
    pass
