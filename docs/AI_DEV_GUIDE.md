# LifeOS v3.2 - AI 開發須知
**給未來接手開發的 AI 閱讀**

---

## 🎯 系統核心理念

### 這是什麼系統？
**問答驅動的第二大腦**，不是記錄工具。

- **核心目標**：自動釐清問題，讓用戶專注發展新專案。
- **核心架構**：雙層記憶系統（Supabase 可變層 + C Kernel 不可變層）。

---

## 💻 技術棧

### Frontend
```
Next.js 14 (App Router) + TypeScript + Tailwind CSS
```

### Backend
```
FastAPI + Python 3.11+ + Pydantic v2
C Kernel (Native Extension for Digital Original)
```

### Database
```
Supabase (PostgreSQL) - 工作副本
Local Binary Files (C Kernel) - 數位原版
```

### AI
```
Google Gemini API (gemini-2.0-flash-exp)
```

---

## 📁 當前目錄結構 (v3.2)

```
lifeosjxs/
├── 📂 frontend-body/          # 前端代碼 (Next.js)
│   ├── app/                   # 頁面主路由
│   ├── components/            # React 組件
│   │   ├── CaptureView.tsx    # 核心：日記輸入
│   │   ├── CardStackDashboard.tsx # 核心：主儀表板
│   │   └── CortexChat.tsx     # 核心：AI 助手
│   └── lib/                   # 工具函數
│
├── 📂 backend-cortex/         # 後端代碼 (FastAPI)
│   ├── kernel/                # C Kernel 源碼
│   │   ├── life_v3.c          # C 核心
│   │   └── storage/           # Kernel 資料
│   ├── routers/               # API 路由
│   │   └── ingest_dual.py     # 雙寫入 API
│   ├── kernel_driver.py       # Python 驅動
│   └── main.py                # 主入口
│
├── 📂 database-hippocampus/   # 資料庫 Schema
│
├── 📂 docs/                   # 文檔中心 (已整理)
│   ├── AI_DEV_GUIDE.md        # 本文件
│   ├── USER_MANUAL.md         # 使用手冊
│   ├── C_KERNEL_GUIDE.md      # C Kernel 指南
│   ├── CLEANUP_PLAN.md        # 清理計畫
│   └── archive/               # 歷史文檔
│
├── 📂 scripts/                # 工具腳本 (cleanup, compile)
└── 📂 node_modules/           # 依賴
```

---

## 📐 編碼規範

### ✅ ALWAYS（總是）
- 使用 Tailwind CSS（所有樣式）
- 使用 TypeScript strict mode
- 使用 Pydantic v2（後端驗證）
- 使用 async/await（I/O 操作）
- 遵循「雙寫入策略」（同時寫入 DB 和 Kernel）

### ❌ NEVER（絕不）
- 使用 inline styles
- 修改 C Kernel 的歷史資料（它是 Append-Only 的）
- 隨意刪除 `docs/` 下的文檔

---

## 🏗️ 系統架構

### 1. 雙寫入策略 (Dual-Write Strategy)
我們實現了「數位原版」概念，確保資料絕對真實且不可篡改。

```python
# Ingest Flow
1. User Input -> API
2. Write to Supabase (Postgres) -> "Working Copy" (Editable, Searchable)
3. Write to C Kernel (Binary)   -> "Digital Original" (Immutable, Append-Only)
```

### 2. C Kernel (Backend Core)
位於 `backend-cortex/kernel/`，負責底層資料存儲。
- `life_v3.c`: 核心實現
- `kernel_driver.py`: Python 驅動
- `life.index` / `life.text`: 二進制儲存

詳細請參閱 `docs/for-ai/C_KERNEL_GUIDE.md`。

---

## 🚀 開發工作流程

### 環境啟動
```bash
# Frontend
cd frontend-body
npm run dev

# Backend
cd backend-cortex
# (Optional) python -m venv venv
# (Optional) source venv/bin/activate
python main.py
```

### 關鍵功能狀態

#### Brain / Graph (待完善)
- 組件保留在 `frontend-body/components/NeuralGraph.tsx` 和 `GraphView.tsx`。
- 目前作為「知識圖譜」的視覺化基礎，尚未完全連接後端。

#### Settings (已修復)
- 使用 `SettingsView.tsx`。
- `SettingsModal.tsx` 已移除，功能合併。
- `Dashboard.tsx` (舊版) 已移除。

---

## 📝 關鍵文件導航

### 文檔 (docs/)
- `AI_DEV_GUIDE.md`: 本文件
- `SYSTEM_CONTEXT.md`: 詳細規範
- `C_KERNEL_GUIDE.md`: C Kernel 指南
- `CODE_CLEANUP_ANALYSIS.md`: 清理分析報告
- `CLEANUP_COMPLETE_REPORT.md`: 清理完成報告

### 後端 (backend-cortex/)
- `main.py`: 入口
- `routers/ingest_dual.py`: 雙寫入邏輯
- `kernel_driver.py`: C Kernel 橋接

### 前端 (frontend-body/)
- `app/page.tsx`: 主頁面
- `components/CaptureView.tsx`: 輸入介面
- `components/CardStackDashboard.tsx`: 主儀表板

---

## 💡 設計哲學

### Digital Originality (數位原版)
Supabase 是為了方便，C Kernel 是為了真實。永遠保留原始數據的二進制備份。

### Question Driven (問答驅動)
系統不該只是被動記錄，而該主動釐清。
架構：Question -> Understanding -> Graph -> Answer -> Clarification

---

**Last Updated**: 2026-02-10
**Version**: 3.2.0
**Status**: Cleaned Up (Phase 1 Complete), C Kernel Integrated
