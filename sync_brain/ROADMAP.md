# LifeOS — 全體 AI 開發路線圖

> **這份文件是開發 AI 的執行手冊**
> 任何 AI 第一次加入 LifeOS 開發，讀完這份文件即可立刻開始工作。
> **最後更新**: 2026-02-27 by Antigravity（主開發 AI）

---

## 🎯 系統使命

**讓蒼禾（指揮官）的生活系統持續進化，同時讓所有參與開發的 AI 都能有效協作。**

> 開發 AI 的核心職責：**規劃優先、交接優先、執行其次**。
> 每次 session 必須更新交接文件，不只是修 bug。

---

## 📋 角色分工

| 角色 | 位置 | 職責 |
|---|---|---|
| **指揮官** | — | 蒼禾，唯一決策者 |
| **主開發 AI** | `tools/` + `sync_brain/` | **架構設計、長遠規劃、交接文件維護** |
| **系統 AI** | `backend-cortex/app/` | 服務使用者 API |
| **其他 AI** | 任意 | 執行任務，留問題 → `sync_brain/QUESTIONS.md` |

---

## ✅ 已完成功能（截至 2026-02-25）

### Core Infrastructure
- [x] **memories 表** — 日記記憶 + VECTOR(3072) embedding 欄位
- [x] **RAG** — `match_memories()` RPC + `hybrid_search()` 混合搜尋
- [x] **Ingest v7.1** — `google.genai` SDK
- [x] **Chat RAG** — 每次對話自動注入相關記憶

### AI Self-Reflection System
- [x] **Phase A~D** — sync_brain 對齊、決策記錄、短期記憶注入、scoring_engine 接通
- [x] **Phase E** — 知識汰換 (Knowledge Decay)，自動封存 30 天未使用的節點
- [x] **Phase F** — 專案語義總結 (Project Synthesis) 與全非同步架構優化
- [x] **Phase G** — (v3.6.4) Backend Supabase Per-Request Client 移轉 (`X-Supabase-Url`) 與 `setup_db.py` 自動化工具
- [x] **Phase H (v3.7.0)** — Header-First Architectural Refinement. Global transient client sync, eliminating config-based 503s.
- [x] **Vector Search** — `match_growth_logs` RPC

### Knowledge Graph（知識圖譜）
- [x] **Crystallizer** — `services/crystallizer.py`，AI 提取 nodes + edges
- [x] **bulk_crystallize.py** — 批次處理歷史記憶（已執行，DB 有 27 nodes / 23 edges）
- [x] **Brain API** — `GET /brain/graph` 合併 memories + nodes + edges
- [x] **NeuralGraph.tsx** — 前端 D3 力導向圖，連接後端

### Project Board（Nomads.com 風格）
- [x] **ProjectCard.tsx** — 彩色狀態條、指標列、厚進度條
- [x] **ProjectDetailPanel.tsx** — 右側滑入，AI 洞察 + 相關日記 + 狀態切換

### Embedding & Search 修復
- [x] **gemini-embedding-001** — 取代 deprecated text-embedding-004（2026-01-14 廢棄）
- [x] **brain.py fallback** — 向量搜尋空時自動改用 ILIKE 關鍵字搜尋
- [x] **Semantic Growth Logs (P3-1)** — `chat.py` 注入相關 lessons 做為決策依據
- [x] **HOME Today Snapshot (P4-2)** — Fixed `memories.py` Bug (APIResponse extraction)
- [x] **Strategic Context (P4-1)** — Injected latest Monthly Review into Cortex system prompt.
- [x] **Enhanced Resilience** — Improved Gemini fallback chain (2.0-flash, 1.5-flash series).
- [x] **Phase P5 (v3.7.4)** — RAG Reranker Sandbox verified (BGE-Reranker-v2-m3).
- [x] **Phase P6 (v3.7.5)** — Agent Skills Infrastructure implemented (Dynamic Skill Loading).
- [x] **Phase P8 (v3.7.6)** — Web Search Capability baseline (duckduckgo-search).

### Dev AI Tooling
- [x] `tools/session_start.py` / `session_end.py` / `search_memory.py`
- [x] `tools/bulk_crystallize.py` — 知識結晶批次工具
- [x] `tools/batch_embed.py` — 歷史 embedding 補做工具 ⭐NEW

---

## 🔴 緊急待辦（影響核心功能）

### 1. 歷史 memories 補做 embedding
**狀態**: 所有舊日記 embedding = NULL，語意搜尋完全無效  
**指令**:
```bash
python tools/batch_embed.py --dry-run    # 先預覽
python tools/batch_embed.py --limit 50  # 每次 50 筆（配額限制）
```
**預計執行次數**: 依日記總筆數，每天上限 ~1500 次 API 呼叫

### 2. 實作 Resilient Database Wrapper (safe_insert)
**狀態**: 背景非同步寫入（如 MonthlyReview, tasks, projects）時常因為 Supabase Schema 漂移 (缺少 `updated_at` 或 `category` 欄位) 拋出 `PGRST204`，導致任務默默失敗。
**目標**: 
- 替 `database.py` 建立全域的 `safe_insert` 函數
- 捕捉 `PGRST204` 錯誤並自動從 payload 中刪除無效欄位後 Retry。
- 根除所有寫入中斷的沉默錯誤。

---

## 🟡 P3：AI 自主性提升（下一個大版本）

### P3-1：Semantic Growth Logs in Chat
`chat.py` `build_system_prompt()` 目前只注入 evolution_log 最後 5 筆（時間排序）  
**強化**：對當前對話語意搜尋 cortex_growth_logs，注入最相關的 3 個 lessons  
**位置**: `backend-cortex/app/api/v1/chat.py`

### P3-2：前端「AI 學習狀態」指示器
在 Chat/Project 頁面 Header 顯示：
```
記憶數: 142    最近決策: 3    準確率: 78%
```
API 來源: `GET /api/v1/memories/count` + `GET /brain/growth/lessons`

### P3-3：Daily Reflection → cortex_growth_logs
`subconscious/daily_reflection.py` 產生的反思目前**未存進 DB**  
**強化**: 將反思結果 + embedding 寫入 `cortex_growth_logs`

---

## 🟢 P4：長遠願景 (三層架構大翻新)

> **🎯 終極型態：日記 = 現實 → HOME = 趨勢 → Project = 意圖**

### P4-1：Diary × Project 自動連動 (最核心)
- [x] **Diary × Project 自動連動 (P4-1)**：寫日記後，AI 自動比對內容，找出已完成的 Tasks 並標記 done，同時更新 Project 的活躍度。
- [x] **戰略脈絡注入**：Cortex 自動讀取 Monthly Review，具備高層級戰略視野。
- **UI 回饋**：ingest 成功後顯示 Toast「✅ 你今天推進了『XXX』，完成了 2 個任務」。

### P4-2：HOME 儀表板重構
- **Today's Snapshot**：首頁頂部顯示「昨日摘要 + 今日待辦數 + 焦點 Project快照」。
- **趨勢意義化**：讓 HOME 的數據能直接反映你到底有沒有在往 Project 目標前進。

### P4-3：Project Board 升級
- **層級化顯示 (Area > Project)**：利用 `parent_id` 欄位，將專屬大方向（如：轉職）與具體項目（如：學 Next.js）分層顯示。
- **知識圖譜雙向綁定**：點擊 Project 可看關聯 Brain 節點，點 Brain 節點可右滑看關聯 Project 面板。

---

---

## 🟢 Phase 4-10: Knowledge & Memory Isolation (Next)

### P10：Memory vs Document Isolation
- [ ] **Schema Definition**: 建立 `documents` 資料表，用於存放外部文獻、技術文件、網頁研究。
- [ ] **RAG Routing**: 修改 `rag_service.py` 支援雙向檢索 (Memory vs Doc)。
- [ ] **Ingest Isolation**: 將日記解析與文件解析流程正式物理隔離。
- [ ] **Semantic Bridging**: 在知識圖譜層級重連文獻與日記。

### Guest Mode (Building in Public)
- [x] **Guest Mode Implementation**: 實作訪客模式。無 API Key 訪客可唯讀檢視公開專案 (is_private=false)。後端強制阻擋寫入，前端隱藏 Capture/Settings 等敏感 UI。

---

---

## 🏗️ 架構原則（所有 AI 必讀）

### 🛑 Critical Safeguards (v3.5.1)

#### 1. Model Name Sanitization
The system is sensitive to Gemini model versioning. **Always use `app.core.gemini.sanitize_model_name()`** before initializing models to prevent 404 errors. Verified Ground Truth IDs (as of 2026-02-28):
- `models/gemini-3.1-pro-preview` (Smart/Latest)
- `models/gemini-2.0-flash-lite` (Fast/Stable)

#### 2. Multi-tier Quota Fallback
If the Smart model reaches quota (429), `chat.py` automatically chain-falls back to `Flash Lite` to ensure continuity.

#### 3. Service Imports
Always import functions like `generate_embedding` individually from `app.services.embedder`. Do NOT attempt to import an `embedder` object as it does not exist in the current service architecture.

#### 4. Embedding & Dimension
All vector data MUST target **3072** dimensions (`gemini-embedding-001`).

---

## 📖 Session SOP

```bash
# 開工
python tools/session_start.py

# 收工（自動追加 evolution_log + commit）
python tools/session_end.py
```

---

**主開發 AI**: Antigravity | **指揮官**: 蒼禾 | **版本**: v3.7.6 (Agent Skills & Search baseline)
