# 開發 AI 交接文檔 — LifeOS (v3.8.6)

> **你是誰**：你是**開發 AI**（Antigravity 或其繼承者），負責擴展和維護 LifeOS 系統。你不是使用者服務 AI（System AI）。

---

## 🏗️ 1. 前後端與資料庫對照表 (The Anatomy Matrix)

當你收到指令時，請優先參考此表定位代碼與數據位位：

| 功能模組 | 前端組件 (`The Body`) | 後端服務 (`The Cortex`) | 資料庫表 (`Hippocampus`) | 內容敘述 |
| :--- | :--- | :--- | :--- | :--- |
| **日記感知** | `CaptureView` | `ingest.py` / `memory_service` | `memories` | 私人日記。關鍵欄位: `mood`, `energy`, `tags`, `local_path` |
| **知識擴展** | `CortexChat` | `rag_service.py` / `search.py` | `documents` | 外部知識。關鍵欄位: `url`, `doc_type`, `embedding(3072)` |
| **神經圖譜** | `NeuralGraph` | `brain.py` / `graph_service` | `nodes`, `edges` | 知識網路。關鍵欄位: `label`, `relation`, `weight` |
| **專案管理** | `ProjectBoard` | `skills/core/projects` | `projects` | 目標計畫。關鍵欄位: `progress`, `due_date`, `parent_id` |
| **行動清單** | `TaskList` | `skills/core/tasks` | `tasks` | 執行任務。關鍵欄位: `project_id`, `source_memory_id` |
| **自我成長** | `SystemStatus` | `growth.py` / `subconscious` | `cortex_growth_logs` | AI 決策紀錄。關鍵欄位: `decision_context`, `ai_prediction` |

---

## 🔄 2. 開發工作流程 (Session Workflow)

為了確保不同 Session 之間的進度不丟失，必須遵守以下協議：

### 🌅 開工啟動 (Session Start)
1. 執行 `python tools/session_start.py`。
2. 閱讀 `sync_brain/evolution_log.json` 最後 5 筆紀錄。
3. 閱讀 `sync_brain/task.md` 確認當前執行中的 Phase 與 Task。
4. 閱讀 `sync_brain/QUESTIONS.md` 檢查是否有遺留問題。

### 🌇 收工交接 (Session End)
1. 執行 `python tools/session_end.py` 並填寫簡明、高信號的摘要。
2. 更新 `sync_brain/task.md` 的 Checkboxes。
3. 如果有重大技術決策或踩坑，務必更新 [SYSTEM_CONTEXT.md](file:///C:/Users/lien.huang/AppData/lifeosjxs/sync_brain/SYSTEM_CONTEXT.md)。
4. `git add . && git commit -m "feat/fix: descriptive message"`

---

## 📋 系統真理地圖 (Truth Map)

| 檔案 | 內容描述 | 重要度 |
|---|---|---|
| [START_HERE.md](file:///C:/Users/lien.huang/AppData/lifeosjxs/sync_brain/START_HERE.md) | **你正在讀的這個檔案 (Single Entry Point)** | 🌟🌟🌟 |
| [HUMAN_AI_AGREEMENT.md](file:///C:/Users/lien.huang/AppData/lifeosjxs/sync_brain/HUMAN_AI_AGREEMENT.md) | **人機協作協議 (架構圖、雙向編輯與溝通標準)** | 🌟🌟🌟 |
| [SYSTEM_CONTEXT.md](file:///C:/Users/lien.huang/AppData/lifeosjxs/sync_brain/SYSTEM_CONTEXT.md) | 系統真理、架構規範、SDK 禁忌與**血淚教訓 (Pitfalls)** | 🌟🌟🌟 |
| [registry.json](file:///C:/Users/lien.huang/AppData/lifeosjxs/sync_brain/registry.json) | Database Schema 基因圖譜 (對齊 Supabase) | 🌟🌟 |
| [evolution_log.json](file:///C:/Users/lien.huang/AppData/lifeosjxs/sync_brain/evolution_log.json) | 系統演化歷史全貌 | 🌟🌟 |
| [ROADMAP.md](file:///C:/Users/lien.huang/AppData/lifeosjxs/sync_brain/ROADMAP.md) | 長遠演化願景與功能規劃 | 🌟 |

---

## 🛠️ 核心開發守則

1. **向量空間**: 全系統統一使用 **3072 維度** (`gemini-embedding-001`)。
2. **Windows 禁忌**: 絕對禁止在 `print()` 輸出 Emoji (會導致 UnicodeEncodeError)。
3. **SDK**: 使用 `app.core.gemini` 作為唯一入口，嚴禁硬編碼模型 ID。
4. **透明化**: 複雜開發前必須提交 `implementation_plan.md` 並使用 `task_boundary` 展示進度。

---
**最後更新**: 2026-03-05 | **系統版本**: v3.8.6
**狀態**: 核心文檔已整合簡化。
