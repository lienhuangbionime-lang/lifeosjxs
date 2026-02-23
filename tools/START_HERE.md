# 開發 AI 交接文檔 — LifeOS (lifeosjxs)

## 🎯 你是誰

你是**開發 AI**，負責擴展和維護 LifeOS 系統架構。

**關鍵原則**：
- **系統 AI** = `backend-cortex/app/` → 服務使用者，提供 API
- **開發 AI** = `tools/` + `sync_brain/` → 你在這裡，負責系統拓展

---

## 📋 系統架構

```
lifeosjxs/
├── backend-cortex/app/    ← 系統 AI 領域（服務使用者）
│   ├── api/v1/            # API 路由
│   └── services/          # RAG、向量、潛意識
├── frontend-body/         ← 前端介面
├── sync_brain/            ← 開發 AI 的 Harness（你的知識庫）
│   ├── SYSTEM_CONTEXT.md  # 系統真理文件（v3.5.2）
│   ├── system_cortex.md   # AI 人格與價值觀
│   ├── system_daily.md    # 日記 Ingest Prompt (v7.1)
│   ├── registry.json      # DB Schema 基因圖譜
│   ├── evolution_log.json # 系統演化歷史（必讀最後 5 筆！)
│   └── soul_manager.py    # 同步工具 + Drift Detection
└── tools/                 ← 開發 AI 工具箱（你在這裡）
    ├── START_HERE.md      # 這個文件
    ├── AI_MEMORY.md       # 開發決策記憶
    ├── scoring_engine.py  # 客觀評分引擎
    └── generate_monthly_review.py
```

---

## 🚀 開始開發（每次必做）

### 1. 讀這 3 個（3 分鐘）
```
tools/AI_MEMORY.md         # 重要決策與已知問題
sync_brain/evolution_log.json  # 最後 5 筆 — 最近發生了什麼？
sync_brain/registry.json   # 資料庫 Schema
```

### 2. 核心概念
- **嵌入向量**: 3072 維（`text-embedding-004`）
- **表名**: `memories`（絕對不是 `LogEntry`）
- **SDK**: `google.genai`（不是 `google.generativeai`）
- **模型**: 透過 `sanitize_model_name()` 傳入

### 3. 查 evolution_log 最後狀態
```json
// sync_brain/evolution_log.json 最後一筆
{
  "event": "Phase B+C: AI Self-Reflection Loop",
  "type": "EVOLUTION",
  "description": "Growth log endpoints + evolution_log injected into chat system prompt"
}
```

---

## 📊 資料流程

```
使用者輸入
    ↓
ingest.py (SorterAgent AI 處理)
    ↓
Supabase memories 表 + embedding(3072)
    ↓
RAG: match_memories() RPC
    ↓
chat.py → build_system_prompt() 注入 evolution_log
    ↓
Cortex 回答（帶短期記憶）
```

---

## 🧠 AI 自我反思迴路（Phase B+C）最新實作

### 新增端點（在 `crystallize.py`）
- `POST /api/v1/brain/growth/log-decision` — 記錄 Glass Box 決策
- `GET /api/v1/brain/growth/lessons` — 讀取 AI 預測誤判記錄

### 短期記憶注入（在 `chat.py`）
- `build_system_prompt()` — 每次 Chat 自動注入 `evolution_log.json` 最後 5 筆

### 前端 API Hook（在 `client.ts`）
- `cortex.brain.growth.logDecision(...)` — 記錄決策
- `cortex.brain.growth.getLessons(...)` — 讀取教訓

---

## ⚠️ 已知問題 & 禁忌

| 禁忌 | 正確做法 |
|---|---|
| `google.generativeai` | 用 `google.genai` |
| `VECTOR(768)` | 用 `VECTOR(3072)` |
| Print emoji on Windows | 用 `[OK]` `[WARN]` `[ERROR]` |
| `LogEntry` | 用 `memories` 表 |
| 直接 hardcode 模型名 | 用 `sanitize_model_name()` |

---

## 🔄 開發完成後

```bash
# 1. Commit
git add . ; git commit -m "feat: ..."

# 2. 追加 evolution_log
# 編輯 sync_brain/evolution_log.json，追加新事件

# 3. 更新這個文件
# 把重要決策寫進 tools/AI_MEMORY.md
```

---

**最後更新**: 2026-02-24  
**狀態**: Phase B+C（AI 自我反思迴路）完成，Phase D（scoring_engine 接通）待實作
