# C Kernel 整合指南
**數位原版 + 工作副本的雙寫入架構**

---

## 🎯 核心理念

### 為什麼必須是 C？

#### 1. 不可變性（Immutability）
```
Supabase: 可以被修改、刪除、篡改
C Kernel: 二進制檔案，Append-Only，真正的不可變
```

#### 2. 數位原版（Digital Original）
```
Supabase: 工作副本（可編輯、可搜尋）
C Kernel: 永久原版（不可篡改、絕對真實）
```

#### 3. 極致性能
```
Python: 毫秒級
C: 微秒級
未來 10 年數據: C 仍然飛快
```

#### 4. 時間不變性
```
content_hash 是永恆的鑰匙
C 語言的二進制結構保證這個承諾
```

---

## 📁 文件結構

```
backend-cortex/
├── kernel/
│   ├── life_v3.c           # C 核心代碼
│   ├── life_v3.so          # 編譯後的函式庫（Linux/Mac）
│   ├── life_v3.dll         # 編譯後的函式庫（Windows）
│   └── storage/            # 資料儲存目錄
│       ├── life.index      # 索引檔案（32 bytes per day）
│       ├── life.text       # 文字內容（Append-Only）
│       └── life.media      # 媒體參考（64 bytes per media）
│
├── kernel_driver.py        # Python 驅動程式
└── routers/
    └── ingest_dual.py      # 雙寫入 API
```

---

## 🚀 快速開始

### Step 1: 編譯 C Kernel

#### Linux/Mac
```bash
cd backend-cortex/kernel
gcc -shared -fPIC -o life_v3.so life_v3.c
```

#### Windows (MinGW)
```bash
cd backend-cortex\kernel
gcc -shared -o life_v3.dll life_v3.c
```

#### Windows (MSVC)
```bash
cd backend-cortex\kernel
cl /LD life_v3.c
```

### Step 2: 測試 C Kernel

```bash
# 編譯測試版本
gcc -DTEST_MODE -o test_kernel life_v3.c
./test_kernel

# 應該看到：
# ✅ Kernel: Day 41 locked successfully.
# Write result: 1
# Read success:
#   Mood: 8
#   Focus: 9
#   Energy: 7
#   Text: 今天完成了 C Kernel 的實現，這是數位原版！
# Testing immutability...
# ⚠️ Kernel Warning: Day 41 is locked. Immutable.
# Second write result: 0 (should be 0)
```

### Step 3: 測試 Python 驅動

```bash
cd backend-cortex
python kernel_driver.py

# 應該看到：
# 🔨 Compiling C Kernel...（如果還沒編譯）
# ✅ Compiled successfully
# ✅ Kernel: Day 41 locked successfully.
# ✅ 日記已鎖定到 C Kernel
# 📖 讀取成功:
#   心情: 8
#   專注: 9
#   能量: 7
#   內容: 今天完成了 C Kernel 的實現，這是數位原版！
```

### Step 4: 整合到 FastAPI

```python
# backend-cortex/main.py

from fastapi import FastAPI
from routers import ingest_dual  # 新增

app = FastAPI()

# 添加雙寫入 router
app.include_router(ingest_dual.router)  # 新增

# ... 其他 routers
```

### Step 5: 測試 API

```bash
# 啟動後端
cd backend-cortex
python -m uvicorn main:app --reload

# 測試寫入
curl -X POST "http://localhost:8000/api/v1/ingest/log" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "今天完成了 C Kernel 整合！",
    "mood": 9,
    "focus": 10,
    "energy": 8,
    "date": "2026-02-10"
  }'

# 應該返回：
# {
#   "status": "synced",
#   "db_id": "xxx",
#   "kernel_locked": true,
#   "kernel_day_offset": 41,
#   "message": "Successfully synced to both Supabase and C Kernel"
# }

# 驗證記錄
curl "http://localhost:8000/api/v1/ingest/verify/2026-02-10"

# 從 C Kernel 讀取
curl "http://localhost:8000/api/v1/ingest/kernel/read/2026-02-10"

# 檢查 Kernel 狀態
curl "http://localhost:8000/api/v1/ingest/kernel/status"
```

---

## 📊 資料流程

### 寫入流程
```
用戶在前端輸入日記
    ↓
POST /api/v1/ingest/log
    ↓
┌─────────────────────────────────┐
│  雙寫入策略                      │
├─────────────────────────────────┤
│  1. 寫入 Supabase (工作副本)    │
│     - 可編輯                     │
│     - 可搜尋                     │
│     - 給前端用                   │
│                                  │
│  2. 寫入 C Kernel (數位原版)    │
│     - 不可變                     │
│     - Append-Only                │
│     - 給自己留底                 │
└─────────────────────────────────┘
    ↓
返回結果
```

### 讀取流程
```
前端請求日記
    ↓
GET /api/v1/memories/{date}
    ↓
從 Supabase 讀取（快速、可搜尋）
    ↓
返回給前端

---

驗證數位原版
    ↓
GET /api/v1/ingest/kernel/read/{date}
    ↓
從 C Kernel 讀取（絕對真實）
    ↓
比對兩者是否一致
```

---

## 🔒 不可變性保證

### C Kernel 的保護機制

#### 1. Append-Only 寫入
```c
// 文字內容只能追加
FILE *ft = fopen(txt_path, "ab");  // "ab" = append binary
fseek(ft, 0, SEEK_END);
uint32_t offset = ftell(ft);
fwrite(text, 1, text_len, ft);
```

#### 2. 覆蓋檢查
```c
// 檢查該天是否已有記錄
DiaryMarker existing;
fread(&existing, sizeof(DiaryMarker), 1, fi);

if (existing.text_len > 0) {
    // 已存在，拒絕覆蓋
    return 0;  // Immutable!
}
```

#### 3. 固定位置索引
```c
// 每天的索引位置固定
fseek(fi, day_offset * sizeof(DiaryMarker), SEEK_SET);
```

### 修改日記的處理

#### 前端修改
```
用戶在前端編輯日記
    ↓
PATCH /api/v1/memories/{id}
    ↓
更新 Supabase（工作副本）
    ↓
C Kernel 保持不變（數位原版）
```

#### 進階：記錄修改歷史
```c
// 如果真的要記錄修改，可以 Append 新版本
typedef struct {
    uint32_t original_day;    // 原始日期
    uint32_t revision_num;    // 修訂版本號
    uint64_t modified_at;     // 修改時間
    uint32_t new_text_offset; // 新文字位置
    uint32_t new_text_len;    // 新文字長度
} RevisionMarker;

// 這樣保留了所有歷史版本
```

---

## 💾 儲存效率

### 資料大小估算

#### 索引檔案（life.index）
```
每天 32 bytes
1 年 = 365 × 32 = 11.7 KB
10 年 = 117 KB
100 年 = 1.17 MB

極致輕量！
```

#### 文字檔案（life.text）
```
假設每天 500 字 = 1.5 KB（UTF-8）
1 年 = 365 × 1.5 KB = 548 KB
10 年 = 5.48 MB
100 年 = 54.8 MB

仍然很小！
```

#### 媒體參考（life.media）
```
每個媒體 64 bytes
假設每天 3 個媒體
1 年 = 365 × 3 × 64 = 70 KB
10 年 = 700 KB
100 年 = 7 MB

元數據極小！
```

### 總計
```
100 年的完整記錄：
- 索引: 1.17 MB
- 文字: 54.8 MB
- 媒體元數據: 7 MB
- 總計: ~63 MB

可以放在 USB 隨身碟裡！
```

---

## 🎯 API 端點

### 寫入
```
POST /api/v1/ingest/log
{
  "content": "日記內容",
  "mood": 8,
  "focus": 9,
  "energy": 7,
  "date": "2026-02-10"  // 可選，預設今天
}

返回：
{
  "status": "synced",           // synced/db_only/kernel_only/failed
  "db_id": "xxx",               // Supabase ID
  "kernel_locked": true,        // C Kernel 是否成功鎖定
  "kernel_day_offset": 41,      // 天數偏移
  "message": "..."
}
```

### 驗證
```
GET /api/v1/ingest/verify/2026-02-10

返回：
{
  "date": "2026-02-10",
  "exists_in_db": true,
  "exists_in_kernel": true,
  "content_match": true,        // 兩者內容是否一致
  "db_length": 500,
  "kernel_length": 500,
  "status": "verified"          // verified/mismatch/partial
}
```

### 讀取數位原版
```
GET /api/v1/ingest/kernel/read/2026-02-10

返回：
{
  "date": "2026-02-10",
  "day_offset": 41,
  "content": "...",
  "metrics": {
    "mood": 8,
    "focus": 9,
    "energy": 7
  },
  "metadata": {
    "text_offset": 12345,
    "text_len": 500,
    "created_at": "2026-02-10T22:00:00",
    "word_count": 0,
    "media_count": 0
  },
  "source": "C Kernel (Digital Original)"
}
```

### Kernel 狀態
```
GET /api/v1/ingest/kernel/status

返回：
{
  "kernel_available": true,
  "index_file_exists": true,
  "text_file_exists": true,
  "index_file_size": 1280,      // bytes
  "text_file_size": 20000,      // bytes
  "estimated_entries": 40,      // 1280 / 32
  "storage_path": "..."
}
```

---

## 🔧 故障排除

### 編譯失敗
```bash
# 確認 gcc 已安裝
gcc --version

# Windows: 安裝 MinGW
# https://sourceforge.net/projects/mingw/

# Mac: 安裝 Xcode Command Line Tools
xcode-select --install

# Linux: 安裝 gcc
sudo apt-get install gcc  # Ubuntu/Debian
sudo yum install gcc      # CentOS/RHEL
```

### Python 找不到 .so/.dll
```python
# 檢查路徑
import os
print(os.path.exists("backend-cortex/kernel/life_v3.so"))

# 手動指定路徑
kernel = LifeKernel(auto_compile=False)
```

### 權限問題
```bash
# Linux/Mac: 給予執行權限
chmod +x backend-cortex/kernel/life_v3.so

# 創建 storage 目錄
mkdir -p backend-cortex/kernel/storage
chmod 755 backend-cortex/kernel/storage
```

---

## 🌟 優勢總結

### C Kernel 的價值
- ✅ **絕對不可變**：Append-Only，歷史不可篡改
- ✅ **極致輕量**：100 年記錄 < 100 MB
- ✅ **極致性能**：微秒級讀寫
- ✅ **數位原版**：永久保存，絕對真實
- ✅ **時間不變性**：content_hash 永恆

### 雙寫入策略的價值
- ✅ **Supabase**：快速搜尋、前端友善
- ✅ **C Kernel**：永久備份、不可篡改
- ✅ **兩全其美**：既有便利性，又有可靠性

---

**現在您擁有了真正的「數位原版」！** 🎉

Supabase 可以隨意編輯，但 C Kernel 永遠記錄著真實的歷史。
