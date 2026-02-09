# LifeOS v3.1 "Autopoiesis" System Architecture

## 1. 專案願景
我們正在開發 LifeOS v3.1，這是一個「生物化」的個人作業系統。
核心概念是 **Autopoiesis (自生系統)**，系統具備感知、記憶、執行與自我進化的能力。

## 2. 系統架構 (The Anatomy)
採用 **Monorepo** 結構，分為四個視窗 (Windows)：

### * **Window 1: The Body (Frontend)**
* **路徑**: `frontend-body/`
* **技術**: Next.js 15, Tailwind CSS (Dark Mode), Lucide Icons.
* **狀態**: 已完成 UI 修復 (Hydration, CSS)、圖譜引擎 (D3 Dynamic Import) 與專案板 (Tag Aggregation)。已植入 `SystemStatus` 元件。
* **部署**: Vercel (已連線 Railway).

### * **Window 2 & 3: The Cortex (Backend)**
* **路徑**: `backend-cortex/`
* **技術**: FastAPI, Python 3.11+, Google Gemini SDK (Pro/Flash), APScheduler.
* **核心功能**:
    * **Sorter Agent**: 負責快速分類輸入。
    * **Architect Agent**: 負責深度思考與對話 (需符合 Pydantic 結構化輸出)。
    * **Evolution Agent**: 負責掃描 Google Model Garden 並自動修改 `.env` 升級模型。
* **部署**: Railway (Docker).

### * **Window 4: The Hippocampus (Database)**
* **技術**: Supabase (PostgreSQL + pgvector).
* **資料**: 存放 Logs (日誌), Tasks (任務), Thoughts (思考軌跡).

## 3. 目前進度 (Current Status)
1. **前端 (Body)**: 已完成重構。`page.tsx` 已整合 Capture, Graph, Project, SystemStatus。解決了 Hydration 與 TypeScript 錯誤。
2. **後端 (Brain)**: 定義了 `backend-cortex` 目錄結構。
3. **進化協議 (Evolution)**:
    * 後端 `api/v1/system.py` 已實作 `POST /upgrade` (修改 .env)。
    * 前端 `SystemStatus.tsx` 已實作 UI 與 API 串接。

## 4. 關鍵準則 (Guidelines)
1. **Gemini API 分層**: 使用 Flash 模型處理感知，Pro 模型處理思考。
2. **結構化輸出**: 所有 Agent 必須透過 Pydantic 定義 `response_schema`。
3. **思考簽名**: AI 回應必須包含 `thought_signature` (觀察、情緒、記憶連結)。

## 5. 下一步任務 (Next Steps)
我們需要開始實作 `backend-cortex` 的核心 Agent 邏輯：
1. 完善 `app/core/gemini.py` (Client 封裝)。
2. 實作 `Architect Agent` 的 Prompt 與邏輯。
3. 讓前端的 `CaptureView` 真正打通到 FastAPI 的 `ingest` 端點。

## 檔案結構 (File Structure)

```
Life-os-v3/
├── README.md                # 📜 [系統宣言] Evolution Protocol 說明
│
├── 📂 frontend-body/        # 🟦 Window 1: The Body (Next.js 15)
│   ├── next.config.js       # ⚙️ 前端運行配置
│   ├── tailwind.config.ts   # 🎨 樣式配置
│   ├── package.json         # 📦 前端依賴管理
│   ├── 📂 app/              # 🚀 [路由中樞]
│   │   ├── globals.css      # 🎨 全域樣式
│   │   ├── layout.tsx       # 🏗️ UI 佈局骨架
│   │   └── page.tsx         # 🏠 系統首頁入口
│   ├── 📂 components/       # 🎨 [視覺模組] 系統交互器官
│   │   ├── CaptureView.tsx  # 📝 AI Terminal (快取輸入)
│   │   ├── ContextModal.tsx # 🗔 上下文彈窗
│   │   ├── Dashboard.tsx    # 📊 主控面板
│   │   ├── GraphView.tsx    # 🕸️ 圖譜視圖
│   │   ├── HistoryView.tsx  # 📜 歷史回溯 (接軌 Memories API)
│   │   ├── NeuralGraph.tsx  # 🧠 神經關聯圖
│   │   ├── ProjectBoard.tsx # 🏗️ 專案管理面板
│   │   ├── SettingsView.tsx # ⚙️ 系統調節
│   │   └── SystemStatus.tsx # 🧬 系統進化 (接軌 System API)
│   └── 📂 lib/              # 🔌 [神經傳導]
│       ├── 📂 ai/           # 🧠 前端 AI 核心函數 (core.ts)
│       └── 📂 api/          # 🌐 API Client (client.ts)
│
├── 📂 backend-cortex/       # 🟧 & 🟪 Window 2 & 3: The Cortex (FastAPI)
│   ├── main.py              # 🚪 應用程式入口 (掛載 Routers & Scheduler)
│   ├── requirements.txt     # 📦 Python 核心依賴 (fastapi, uvicorn, supabase, google-genai)
│   ├── .env                 # 🔑 [私鑰] GEMINI_API_KEY, SUPABASE_URL/KEY
│   └── 📂 app/              # 🧠 [大腦邏輯層]
│       ├── 📂 core/         # ⚙️ [核心基礎設施]
│       │   ├── config.py    # 🔧 環境變數管理
│       │   ├── database.py  # 💾 Database Client (supabase-py 單例)
│       │   └── gemini.py    # 🤖 Model Factory (Client 初始化 & get_model)
│       ├── 📂 models/       # 📐 [資料結構]
│       │   └── schemas.py   # 📝 Pydantic Models (LogEntry, API Response)
│       ├── 📂 api/          # 🌐 [皮質接口] (Routers)
│       │   └── 📂 v1/
│       │       ├── ingest.py    # 📥 感知輸入 (處理 CaptureView)
│       │       ├── memories.py  # 💾 記憶檢索 (處理 HistoryView)
│       │       └── system.py    # 🧬 系統狀態 (處理 SystemStatus)
│       └── 📂 subconscious/ # 🌑 [潛意識循環]
│           └── scheduler.py # ⏰ 生物時鐘 (APScheduler 心跳與排程)
│
└── 📂 database-hippocampus/ # 🟩 Window 4: The Hippocampus
    └── 📂 prisma/           # 📐 [核心記憶模板]
        └── schema.prisma    # 📝 唯一記憶真理來源 (Schema Definition Only)
```