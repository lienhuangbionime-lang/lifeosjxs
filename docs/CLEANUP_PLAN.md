# LifeOS 目錄清理方案
**當前大小：~1GB → 目標：<100MB（不含 node_modules）**

---

## 📊 當前狀況分析

### 目錄大小
```
frontend-body:        500.58 MB  ⚠️ 過大
backend-cortex:       340.01 MB  ⚠️ 過大
node_modules:         135.30 MB  ✅ 正常（開發依賴）
.next:                124.74 MB  ⚠️ 可刪除（編譯產物）
database-hippocampus:   0.00 MB  ✅ 正常
文檔:                  ~10 MB   ⚠️ 過多

總計: ~1100 MB
```

---

## 🎯 必須保留的目錄結構

```
lifeosjxs/
├── frontend-body/              # 前端代碼
│   ├── app/                    # ✅ 保留：Next.js 頁面
│   ├── components/             # ✅ 保留：React 組件
│   ├── lib/                    # ✅ 保留：工具函數
│   ├── public/                 # ⚠️ 檢查：靜態資源（可能有大文件）
│   ├── styles/                 # ✅ 保留：樣式
│   ├── package.json            # ✅ 保留
│   ├── tsconfig.json           # ✅ 保留
│   ├── tailwind.config.ts      # ✅ 保留
│   └── next.config.js          # ✅ 保留
│
├── backend-cortex/             # 後端代碼
│   ├── routers/                # ✅ 保留：API 路由
│   ├── models/                 # ✅ 保留：數據模型
│   ├── services/               # ✅ 保留：業務邏輯
│   ├── kernel/                 # ✅ 保留：C Kernel
│   │   ├── life_v3.c           # ✅ 保留
│   │   ├── compile.bat         # ✅ 保留
│   │   ├── compile.sh          # ✅ 保留
│   │   └── storage/            # ✅ 保留（資料目錄）
│   ├── kernel_driver.py        # ✅ 保留
│   ├── media_core.py           # ✅ 保留
│   ├── main.py                 # ✅ 保留
│   ├── requirements.txt        # ✅ 保留
│   └── __pycache__/            # ❌ 刪除：Python 緩存
│
├── database-hippocampus/       # 資料庫
│   └── schema.sql              # ✅ 保留
│
├── node_modules/               # ✅ 保留：開發依賴（但可重新安裝）
│
├── .next/                      # ❌ 刪除：編譯產物（可重新生成）
│
├── .git/                       # ✅ 保留：版本控制
│
├── 文檔/                       # ⚠️ 精簡
│   ├── AI_DEV_GUIDE.md         # ✅ 保留：核心文檔
│   ├── USER_MANUAL.md          # ✅ 保留：核心文檔
│   ├── README_DOCS.md          # ✅ 保留：索引
│   ├── C_KERNEL_GUIDE.md       # ✅ 保留：重要
│   ├── SYSTEM_CONTEXT.md       # ✅ 保留：重要
│   ├── QUESTION_DRIVEN_ARCHITECTURE.md  # ✅ 保留：重要
│   └── 其他 .md                # ⚠️ 移到 docs/ 目錄
│
├── .cursorrules                # ✅ 保留
├── .gitignore                  # ✅ 保留
├── README.md                   # ✅ 保留
├── package.json                # ✅ 保留（如果有）
└── .env.shared                 # ✅ 保留
```

---

## 🗑️ 需要刪除/清理的內容

### 1. 編譯產物（可重新生成）
```
❌ .next/                       # 124.74 MB
❌ backend-cortex/__pycache__/  # Python 緩存
❌ backend-cortex/**/*.pyc      # Python 編譯文件
❌ frontend-body/.next/         # 如果存在
```

### 2. 可能的大文件（需檢查）
```
⚠️ frontend-body/public/        # 可能有大圖片/影片
⚠️ backend-cortex/uploads/      # 可能有上傳的文件
⚠️ backend-cortex/logs/         # 可能有日誌文件
⚠️ backend-cortex/temp/         # 臨時文件
```

### 3. 重複或過時的文檔
```
❌ AI_FLOATING_ASSISTANT_UPDATE.md
❌ ANALYSIS_DISPLAY_FIX.md
❌ CARD_STACK_DASHBOARD.md
❌ CARD_STACK_QUICK_START.md
❌ CONTEXT_ENGINEERING_COMPLETE.md
❌ CONTEXT_ENGINEERING_GUIDE.md
❌ CONTEXT_ENGINEERING_QUICKSTART.md
❌ CORTEXCHAT_CONNECTION_FIX.md
❌ EMBEDDING_MODEL_FIX.md
❌ ERROR_RESOLUTION_REPORT.txt
❌ FIX_SUMMARY.md
❌ MEDIA_CORE_ARCHITECTURE.h
❌ MEDIA_CORE_INTEGRATION.md
❌ MEDIA_CORE_NOMAD_SUMMARY.md
❌ MOBILE_DRAG_FIX.md
❌ NOMAD_LIST_STYLE_DESIGN.md
❌ QUICK_FIX.md
❌ RUNTIME_ERROR_FIX.md
❌ SESSION_COMPLETE_SUMMARY.md
❌ UI_FIX_CAPTUREVIEW.md

→ 移到 docs/archive/ 目錄
```

---

## 📁 建議的最終目錄結構

```
lifeosjxs/
├── frontend-body/              # 前端代碼
├── backend-cortex/             # 後端代碼
├── database-hippocampus/       # 資料庫
├── docs/                       # 📁 新建：文檔目錄
│   ├── AI_DEV_GUIDE.md         # 核心文檔
│   ├── USER_MANUAL.md          # 核心文檔
│   ├── C_KERNEL_GUIDE.md       # 核心文檔
│   ├── SYSTEM_CONTEXT.md       # 核心文檔
│   ├── QUESTION_DRIVEN_ARCHITECTURE.md
│   ├── README_DOCS.md          # 索引
│   └── archive/                # 歷史文檔
│       ├── AI_FLOATING_ASSISTANT_UPDATE.md
│       ├── CARD_STACK_DASHBOARD.md
│       └── ... (其他舊文檔)
│
├── .cursorrules
├── .gitignore
├── README.md
└── .env.shared
```

---

## 🚀 清理步驟

### Step 1: 刪除編譯產物
```powershell
# 刪除 .next
Remove-Item -Path ".next" -Recurse -Force

# 刪除 Python 緩存
Get-ChildItem -Path "backend-cortex" -Recurse -Include "__pycache__","*.pyc" | Remove-Item -Recurse -Force
```

### Step 2: 創建 docs 目錄並移動文檔
```powershell
# 創建目錄
New-Item -Path "docs" -ItemType Directory
New-Item -Path "docs/archive" -ItemType Directory

# 移動核心文檔
Move-Item -Path "AI_DEV_GUIDE.md" -Destination "docs/"
Move-Item -Path "USER_MANUAL.md" -Destination "docs/"
Move-Item -Path "C_KERNEL_GUIDE.md" -Destination "docs/"
Move-Item -Path "SYSTEM_CONTEXT.md" -Destination "docs/"
Move-Item -Path "QUESTION_DRIVEN_ARCHITECTURE.md" -Destination "docs/"
Move-Item -Path "README_DOCS.md" -Destination "docs/"

# 移動歷史文檔到 archive
Move-Item -Path "AI_FLOATING_ASSISTANT_UPDATE.md" -Destination "docs/archive/"
Move-Item -Path "ANALYSIS_DISPLAY_FIX.md" -Destination "docs/archive/"
Move-Item -Path "CARD_STACK_DASHBOARD.md" -Destination "docs/archive/"
Move-Item -Path "CARD_STACK_QUICK_START.md" -Destination "docs/archive/"
Move-Item -Path "CONTEXT_ENGINEERING_COMPLETE.md" -Destination "docs/archive/"
Move-Item -Path "CONTEXT_ENGINEERING_GUIDE.md" -Destination "docs/archive/"
Move-Item -Path "CONTEXT_ENGINEERING_QUICKSTART.md" -Destination "docs/archive/"
Move-Item -Path "CORTEXCHAT_CONNECTION_FIX.md" -Destination "docs/archive/"
Move-Item -Path "EMBEDDING_MODEL_FIX.md" -Destination "docs/archive/"
Move-Item -Path "ERROR_RESOLUTION_REPORT.txt" -Destination "docs/archive/"
Move-Item -Path "FIX_SUMMARY.md" -Destination "docs/archive/"
Move-Item -Path "MEDIA_CORE_ARCHITECTURE.h" -Destination "docs/archive/"
Move-Item -Path "MEDIA_CORE_INTEGRATION.md" -Destination "docs/archive/"
Move-Item -Path "MEDIA_CORE_NOMAD_SUMMARY.md" -Destination "docs/archive/"
Move-Item -Path "MOBILE_DRAG_FIX.md" -Destination "docs/archive/"
Move-Item -Path "NOMAD_LIST_STYLE_DESIGN.md" -Destination "docs/archive/"
Move-Item -Path "QUICK_FIX.md" -Destination "docs/archive/"
Move-Item -Path "RUNTIME_ERROR_FIX.md" -Destination "docs/archive/"
Move-Item -Path "SESSION_COMPLETE_SUMMARY.md" -Destination "docs/archive/"
Move-Item -Path "UI_FIX_CAPTUREVIEW.md" -Destination "docs/archive/"
```

### Step 3: 檢查並清理大文件
```powershell
# 查找大於 1MB 的文件
Get-ChildItem -Path "." -Recurse -File -ErrorAction SilentlyContinue | 
    Where-Object { $_.Length -gt 1MB } | 
    Select-Object FullName, @{Name="SizeMB";Expression={[math]::Round($_.Length/1MB, 2)}} | 
    Sort-Object SizeMB -Descending | 
    Format-Table -AutoSize
```

### Step 4: 更新 .gitignore
```
# 添加到 .gitignore
.next/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.dll
*.dylib
node_modules/
.env.local
backend-cortex/kernel/storage/*.index
backend-cortex/kernel/storage/*.text
backend-cortex/kernel/storage/*.media
```

---

## 📊 預期結果

### 清理前
```
frontend-body:        500.58 MB
backend-cortex:       340.01 MB
node_modules:         135.30 MB
.next:                124.74 MB
文檔:                  ~10 MB
總計:                ~1110 MB
```

### 清理後
```
frontend-body:        ~50 MB   (移除 .next, public 中的大文件)
backend-cortex:       ~20 MB   (移除 __pycache__, 大文件)
node_modules:         135 MB   (保留，但可選擇性刪除後重裝)
docs:                 ~5 MB    (整理後的文檔)
總計:                ~210 MB  (不含 node_modules)
                     ~75 MB   (如果刪除 node_modules)
```

---

## ⚠️ 注意事項

### 可以安全刪除（可重新生成）
- ✅ `.next/` - 執行 `npm run build` 重新生成
- ✅ `__pycache__/` - Python 自動生成
- ✅ `node_modules/` - 執行 `npm install` 重新安裝

### 絕對不能刪除
- ❌ `frontend-body/app/`
- ❌ `frontend-body/components/`
- ❌ `backend-cortex/routers/`
- ❌ `backend-cortex/kernel/life_v3.c`
- ❌ `backend-cortex/kernel_driver.py`
- ❌ `.git/`
- ❌ `package.json`
- ❌ `requirements.txt`

---

## 🎯 執行確認

請確認以下操作：

1. ✅ 刪除 `.next/` 目錄（124.74 MB）
2. ✅ 刪除 `__pycache__/` 和 `*.pyc`
3. ✅ 創建 `docs/` 目錄
4. ✅ 移動核心文檔到 `docs/`
5. ✅ 移動歷史文檔到 `docs/archive/`
6. ⚠️ 檢查 `frontend-body/public/` 中的大文件
7. ⚠️ 檢查 `backend-cortex/` 中的大文件

**確認後我將開始執行清理操作。**
