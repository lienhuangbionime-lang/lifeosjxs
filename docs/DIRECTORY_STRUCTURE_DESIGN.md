# LifeOS 目錄結構設計
**AI / 使用者 / 程式 三層分類系統**

---

## 🎯 設計理念

### 三大角色
```
1. AI 開發者：需要技術文檔和開發指南
2. 使用者：需要使用手冊和快速指南
3. 程式本身：源代碼、配置、資料
```

---

## 📁 建議的目錄結構

```
lifeosjxs/
│
├── 📂 src/                          # 程式源代碼
│   ├── frontend/                    # 前端代碼
│   │   ├── app/                     # Next.js 頁面
│   │   ├── components/              # React 組件
│   │   ├── lib/                     # 工具函數
│   │   ├── styles/                  # 樣式
│   │   └── public/                  # 靜態資源
│   │
│   ├── backend/                     # 後端代碼
│   │   ├── routers/                 # API 路由
│   │   ├── models/                  # 數據模型
│   │   ├── services/                # 業務邏輯
│   │   ├── kernel/                  # C Kernel
│   │   │   ├── life_v3.c
│   │   │   ├── compile.bat
│   │   │   ├── compile.sh
│   │   │   └── storage/             # 資料儲存
│   │   ├── kernel_driver.py
│   │   ├── media_core.py
│   │   └── main.py
│   │
│   └── database/                    # 資料庫
│       └── schema.sql
│
├── 📂 docs/                         # 文檔中心
│   ├── 📂 for-ai/                   # 給 AI 開發者
│   │   ├── AI_DEV_GUIDE.md          # ⭐ AI 開發須知
│   │   ├── SYSTEM_CONTEXT.md        # ⭐ 系統上下文
│   │   ├── QUESTION_DRIVEN_ARCHITECTURE.md  # 架構設計
│   │   ├── C_KERNEL_GUIDE.md        # C Kernel 指南
│   │   └── API_REFERENCE.md         # API 參考（待建立）
│   │
│   ├── 📂 for-users/                # 給使用者
│   │   ├── USER_MANUAL.md           # ⭐ 使用手冊
│   │   ├── QUICK_START.md           # 快速開始（待建立）
│   │   ├── FAQ.md                   # 常見問題（待建立）
│   │   └── CHANGELOG.md             # 更新日誌（待建立）
│   │
│   ├── 📂 archive/                  # 歷史文檔
│   │   ├── fixes/                   # 修復記錄
│   │   │   ├── MOBILE_DRAG_FIX.md
│   │   │   ├── EMBEDDING_MODEL_FIX.md
│   │   │   └── ...
│   │   ├── features/                # 功能開發記錄
│   │   │   ├── CARD_STACK_DASHBOARD.md
│   │   │   ├── AI_FLOATING_ASSISTANT_UPDATE.md
│   │   │   └── ...
│   │   └── sessions/                # 開發會話記錄
│   │       ├── SESSION_COMPLETE_SUMMARY.md
│   │       └── ...
│   │
│   └── README.md                    # 文檔索引
│
├── 📂 config/                       # 配置文件
│   ├── .cursorrules                 # Cursor AI 規則
│   ├── .env.shared                  # 環境變數範本
│   ├── .gitignore
│   ├── tsconfig.json                # TypeScript 配置
│   ├── tailwind.config.ts           # Tailwind 配置
│   ├── next.config.js               # Next.js 配置
│   └── requirements.txt             # Python 依賴
│
├── 📂 data/                         # 資料目錄
│   ├── kernel/                      # C Kernel 資料
│   │   ├── life.index               # 索引檔案
│   │   ├── life.text                # 文字內容
│   │   └── life.media               # 媒體參考
│   ├── uploads/                     # 上傳的文件
│   └── cache/                       # 緩存
│
├── 📂 scripts/                      # 工具腳本
│   ├── cleanup.ps1                  # 清理腳本
│   ├── setup.ps1                    # 初始化腳本
│   └── deploy.sh                    # 部署腳本
│
├── 📂 tests/                        # 測試
│   ├── frontend/
│   └── backend/
│
├── node_modules/                    # Node.js 依賴（.gitignore）
├── .next/                           # Next.js 編譯產物（.gitignore）
├── .git/                            # Git 版本控制
│
├── README.md                        # 專案說明
├── package.json                     # Node.js 配置
└── LICENSE                          # 授權文件
```

---

## 🎨 分類邏輯

### 1. **src/** - 程式源代碼
**誰用**：開發者（人類 + AI）  
**內容**：所有可執行的代碼  
**原則**：
- ✅ 只放源代碼
- ✅ 按功能分類（frontend/backend/database）
- ✅ 清晰的模組化結構

### 2. **docs/** - 文檔中心
**誰用**：AI 開發者 + 使用者  
**內容**：所有文檔  
**原則**：
- ✅ 按受眾分類（for-ai / for-users）
- ✅ 歷史文檔歸檔（archive）
- ✅ 核心文檔置頂

#### 2.1 **docs/for-ai/** - AI 開發者專用
```
目標：讓 AI 快速理解系統並生成正確代碼

必讀文檔：
1. AI_DEV_GUIDE.md          - 快速開始（5 分鐘）
2. SYSTEM_CONTEXT.md        - 完整上下文（15 分鐘）
3. QUESTION_DRIVEN_ARCHITECTURE.md  - 架構設計

參考文檔：
- C_KERNEL_GUIDE.md         - C Kernel 詳細說明
- API_REFERENCE.md          - API 端點參考
```

#### 2.2 **docs/for-users/** - 使用者專用
```
目標：讓使用者快速上手並解決問題

必讀文檔：
1. USER_MANUAL.md           - 完整使用手冊
2. QUICK_START.md           - 3 分鐘快速開始

參考文檔：
- FAQ.md                    - 常見問題
- CHANGELOG.md              - 更新日誌
```

#### 2.3 **docs/archive/** - 歷史文檔
```
目標：保留開發歷史，但不影響日常使用

分類：
- fixes/        - 修復記錄
- features/     - 功能開發記錄
- sessions/     - 開發會話記錄
```

### 3. **config/** - 配置文件
**誰用**：開發者 + 部署系統  
**內容**：所有配置  
**原則**：
- ✅ 集中管理
- ✅ 環境變數分離
- ✅ 版本控制

### 4. **data/** - 資料目錄
**誰用**：程式運行時  
**內容**：運行時產生的資料  
**原則**：
- ✅ 不納入版本控制（.gitignore）
- ✅ 按類型分類（kernel/uploads/cache）
- ✅ 定期備份

### 5. **scripts/** - 工具腳本
**誰用**：開發者  
**內容**：自動化腳本  
**原則**：
- ✅ 命名清晰
- ✅ 跨平台支持
- ✅ 文檔化

---

## 🚀 遷移計劃

### Step 1: 創建新目錄結構
```powershell
# 創建主要目錄
New-Item -Path "src" -ItemType Directory
New-Item -Path "src/frontend" -ItemType Directory
New-Item -Path "src/backend" -ItemType Directory
New-Item -Path "src/database" -ItemType Directory

New-Item -Path "docs/for-ai" -ItemType Directory
New-Item -Path "docs/for-users" -ItemType Directory
New-Item -Path "docs/archive/fixes" -ItemType Directory
New-Item -Path "docs/archive/features" -ItemType Directory
New-Item -Path "docs/archive/sessions" -ItemType Directory

New-Item -Path "config" -ItemType Directory
New-Item -Path "data/kernel" -ItemType Directory
New-Item -Path "data/uploads" -ItemType Directory
New-Item -Path "data/cache" -ItemType Directory
New-Item -Path "scripts" -ItemType Directory
```

### Step 2: 移動源代碼
```powershell
# 移動前端
Move-Item -Path "frontend-body/*" -Destination "src/frontend/"

# 移動後端
Move-Item -Path "backend-cortex/*" -Destination "src/backend/"

# 移動資料庫
Move-Item -Path "database-hippocampus/*" -Destination "src/database/"
```

### Step 3: 移動文檔
```powershell
# AI 開發者文檔
Move-Item -Path "AI_DEV_GUIDE.md" -Destination "docs/for-ai/"
Move-Item -Path "SYSTEM_CONTEXT.md" -Destination "docs/for-ai/"
Move-Item -Path "QUESTION_DRIVEN_ARCHITECTURE.md" -Destination "docs/for-ai/"
Move-Item -Path "C_KERNEL_GUIDE.md" -Destination "docs/for-ai/"

# 使用者文檔
Move-Item -Path "USER_MANUAL.md" -Destination "docs/for-users/"

# 歷史文檔 - 修復記錄
Move-Item -Path "MOBILE_DRAG_FIX.md" -Destination "docs/archive/fixes/"
Move-Item -Path "EMBEDDING_MODEL_FIX.md" -Destination "docs/archive/fixes/"
Move-Item -Path "CORTEXCHAT_CONNECTION_FIX.md" -Destination "docs/archive/fixes/"
# ... 其他修復記錄

# 歷史文檔 - 功能記錄
Move-Item -Path "CARD_STACK_DASHBOARD.md" -Destination "docs/archive/features/"
Move-Item -Path "AI_FLOATING_ASSISTANT_UPDATE.md" -Destination "docs/archive/features/"
# ... 其他功能記錄

# 歷史文檔 - 會話記錄
Move-Item -Path "SESSION_COMPLETE_SUMMARY.md" -Destination "docs/archive/sessions/"
```

### Step 4: 移動配置
```powershell
Move-Item -Path ".cursorrules" -Destination "config/"
Move-Item -Path ".env.shared" -Destination "config/"
Move-Item -Path "tsconfig.json" -Destination "config/" -ErrorAction SilentlyContinue
Move-Item -Path "tailwind.config.ts" -Destination "config/" -ErrorAction SilentlyContinue
Move-Item -Path "next.config.js" -Destination "config/" -ErrorAction SilentlyContinue
Move-Item -Path "requirements.txt" -Destination "config/" -ErrorAction SilentlyContinue
```

### Step 5: 移動資料
```powershell
# 移動 C Kernel 資料
Move-Item -Path "src/backend/kernel/storage/*" -Destination "data/kernel/"
```

### Step 6: 移動腳本
```powershell
Move-Item -Path "cleanup.ps1" -Destination "scripts/"
Move-Item -Path "src/backend/kernel/compile.bat" -Destination "scripts/"
Move-Item -Path "src/backend/kernel/compile.sh" -Destination "scripts/"
```

---

## 📝 更新配置文件

### package.json
```json
{
  "scripts": {
    "dev": "cd src/frontend && next dev",
    "build": "cd src/frontend && next build",
    "start": "cd src/frontend && next start"
  }
}
```

### Python 路徑更新
```python
# src/backend/main.py
# 更新所有相對路徑
```

---

## 🎯 優勢

### 1. 清晰的職責分離
```
src/        → 程式代碼
docs/       → 文檔
config/     → 配置
data/       → 資料
scripts/    → 工具
```

### 2. 受眾導向
```
docs/for-ai/     → AI 開發者快速找到需要的文檔
docs/for-users/  → 使用者快速找到使用手冊
docs/archive/    → 歷史記錄不干擾日常使用
```

### 3. 易於維護
```
新增 AI 文檔 → 放到 docs/for-ai/
新增使用手冊 → 放到 docs/for-users/
修復記錄     → 放到 docs/archive/fixes/
```

### 4. 易於備份
```
備份代碼 → src/
備份資料 → data/
備份文檔 → docs/
```

---

## ✅ 建議執行順序

1. **先創建新目錄結構**（不移動文件）
2. **測試新結構是否合理**
3. **逐步移動文件**（先移動文檔，再移動代碼）
4. **更新配置和路徑**
5. **測試程式是否正常運行**
6. **刪除舊目錄**

---

**這個結構清晰、專業、易於維護！您覺得如何？**
