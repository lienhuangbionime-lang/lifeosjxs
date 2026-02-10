# Media Core 整合指南
**如何將 C-style Media Core 整合到 LifeOS**

---

## ✅ 已完成

### 1. Python 實現
**文件**: `backend-cortex/media_core.py`

核心功能：
- ✅ MediaRef（64-byte 結構）
- ✅ DiaryMarker（32-byte 結構）
- ✅ LocationRef（位置追蹤）
- ✅ BiometricRef（生物識別）
- ✅ MediaChain（鏈結串列管理）
- ✅ 二進制序列化（to_bytes/from_bytes）

### 2. FastAPI 整合
**文件**: `backend-cortex/routers/media.py`

API 端點：
- ✅ POST `/api/v1/media/upload` - 上傳媒體
- ✅ GET `/api/v1/media/diary/{date}` - 獲取日記 + 媒體
- ✅ GET `/api/v1/media/timeline` - 獲取時間軸
- ✅ DELETE `/api/v1/media/{content_hash}` - 刪除媒體

---

## 🚀 快速整合步驟

### Step 1: 在 main.py 中添加 router

```python
# backend-cortex/main.py

from fastapi import FastAPI
from routers import media  # 新增

app = FastAPI()

# 添加 media router
app.include_router(media.router)  # 新增

# ... 其他 routers
```

### Step 2: 測試 API

```bash
# 啟動後端
cd backend-cortex
python -m uvicorn main:app --reload

# 測試上傳
curl -X POST "http://localhost:8000/api/v1/media/upload" \
  -F "file=@test.jpg" \
  -F "media_type=image" \
  -F "date=2026-02-10"

# 測試查詢
curl "http://localhost:8000/api/v1/media/diary/2026-02-10"
```

### Step 3: 前端整合

```typescript
// frontend-body/lib/api/media.ts

export const mediaAPI = {
  async uploadMedia(file: File, type: string, date: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('media_type', type);
    formData.append('date', date);
    
    const response = await fetch('http://localhost:8000/api/v1/media/upload', {
      method: 'POST',
      body: formData,
    });
    
    return response.json();
  },
  
  async getDiaryWithMedia(date: string) {
    const response = await fetch(`http://localhost:8000/api/v1/media/diary/${date}`);
    return response.json();
  },
};
```

---

## 📊 資料流程

### 上傳媒體
```
用戶上傳檔案
    ↓
Frontend (FormData)
    ↓
FastAPI (media.py)
    ↓
創建 MediaRef
    ↓
儲存檔案（本機/S3）
    ↓
添加到 MediaChain
    ↓
返回 URL
```

### 查詢日記
```
用戶請求日期
    ↓
Frontend
    ↓
FastAPI (media.py)
    ↓
讀取 DiaryMarker
    ↓
讀取 MediaChain
    ↓
構建完整回應
    ↓
返回 JSON
```

---

## 💾 儲存方案

### 方案 1: 本機儲存（推薦，因為只有你使用）

```python
# media_core.py

import os
from pathlib import Path

MEDIA_ROOT = Path("./media_storage")

async def save_to_local(content: bytes, content_hash: UUID, path: str) -> str:
    """儲存到本機"""
    # 創建目錄
    full_path = MEDIA_ROOT / path
    full_path.mkdir(parents=True, exist_ok=True)
    
    # 儲存檔案
    file_path = full_path / f"{content_hash}"
    with open(file_path, 'wb') as f:
        f.write(content)
    
    return str(file_path)
```

### 方案 2: Supabase Storage（如果需要雲端）

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def save_to_supabase(content: bytes, content_hash: UUID, path: str) -> str:
    """儲存到 Supabase Storage"""
    bucket_name = "lifeos-media"
    file_path = f"{path}/{content_hash}"
    
    # 上傳
    supabase.storage.from_(bucket_name).upload(
        file_path,
        content
    )
    
    # 獲取 URL
    url = supabase.storage.from_(bucket_name).get_public_url(file_path)
    return url
```

---

## 🗄️ 資料庫整合

### 選項 1: 直接存二進制（簡單）

```sql
-- Supabase
CREATE TABLE media_refs (
    content_hash UUID PRIMARY KEY,
    data BYTEA,  -- 64 bytes 的二進制資料
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE diary_markers (
    date DATE PRIMARY KEY,
    data BYTEA,  -- 32 bytes 的二進制資料
    text_content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

```python
# 儲存
media_bytes = media.to_bytes()
supabase.table('media_refs').insert({
    'content_hash': str(media.content_hash),
    'data': media_bytes
}).execute()

# 讀取
result = supabase.table('media_refs').select('*').eq('content_hash', str(content_hash)).execute()
media = MediaRef.from_bytes(result.data[0]['data'])
```

### 選項 2: 存 JSON（靈活）

```sql
-- Supabase
CREATE TABLE media_refs (
    content_hash UUID PRIMARY KEY,
    media_type TEXT,
    storage_class TEXT,
    duration_sec INTEGER,
    file_size_kb INTEGER,
    storage_path TEXT,
    width INTEGER,
    height INTEGER,
    next_ptr UUID,
    prev_ptr UUID,
    created_at TIMESTAMP DEFAULT NOW()
);
```

```python
# 儲存
supabase.table('media_refs').insert({
    'content_hash': str(media.content_hash),
    'media_type': media.media_type.name,
    'storage_class': media.storage_class.name,
    'duration_sec': media.duration_sec,
    # ... 其他欄位
}).execute()
```

---

## 🎯 推薦方案（因為只有你使用）

### 簡化版本
```
1. 媒體檔案：存本機（./media_storage/）
2. 元數據：存 Supabase（JSON 格式）
3. 文字內容：存 Supabase（TEXT 欄位）
```

### 為什麼？
- ✅ 簡單易維護
- ✅ 不需要複雜的二進制處理
- ✅ Supabase 查詢方便
- ✅ 本機檔案備份容易

### 實現
```python
# media_core.py

class MediaStorage:
    """簡化的媒體儲存"""
    
    def __init__(self):
        self.media_root = Path("./media_storage")
        self.media_root.mkdir(exist_ok=True)
    
    async def save_media(self, file_content: bytes, media: MediaRef) -> str:
        """儲存媒體檔案"""
        # 創建日期目錄
        date_path = self.media_root / media.storage_path
        date_path.mkdir(parents=True, exist_ok=True)
        
        # 儲存檔案
        file_path = date_path / str(media.content_hash)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 儲存元數據到 Supabase
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        supabase.table('media_refs').insert({
            'content_hash': str(media.content_hash),
            'media_type': media.media_type.name,
            'storage_class': media.storage_class.name,
            'duration_sec': media.duration_sec,
            'file_size_kb': media.file_size_kb,
            'storage_path': media.storage_path,
            'width': media.width,
            'height': media.height,
        }).execute()
        
        return str(file_path)
    
    async def get_media(self, content_hash: UUID) -> MediaRef:
        """讀取媒體元數據"""
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        result = supabase.table('media_refs').select('*').eq(
            'content_hash', str(content_hash)
        ).execute()
        
        data = result.data[0]
        return MediaRef(
            content_hash=UUID(data['content_hash']),
            media_type=MediaType[data['media_type']],
            storage_class=StorageClass[data['storage_class']],
            duration_sec=data['duration_sec'],
            file_size_kb=data['file_size_kb'],
            storage_path=data['storage_path'],
            width=data['width'],
            height=data['height'],
        )
```

---

## ✅ 下一步

### 立即可做
1. 在 `main.py` 添加 media router
2. 創建 `media_storage/` 目錄
3. 測試上傳 API

### 本週可做
1. 實現本機儲存
2. 整合 Supabase
3. 前端上傳功能

### 未來可做
1. S3 儲存（如果需要）
2. IPFS 儲存（去中心化）
3. 壓縮和優化

---

## 💡 關鍵優勢

### C-style 設計的好處
- ✅ 極致輕量（64 bytes per media）
- ✅ 可預測的大小
- ✅ 高性能（cache-friendly）
- ✅ 可以直接存二進制

### Python 實現的好處
- ✅ 易於整合 FastAPI
- ✅ 易於維護
- ✅ 保留核心設計理念
- ✅ 可以隨時轉回 C（如果需要）

---

**現在 Media Core 已經準備好整合到 LifeOS 了！** 🚀

只需要在 `main.py` 添加一行代碼即可開始使用。
