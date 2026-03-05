# LifeOS — 關鍵路徑保護清單 (CRITICAL_PATHS.md)

> **任何 Gemini Flash 在修改下列文件前，必須先閱讀此文件，並在 `QUESTIONS.md` 中確認影響範圍。**

---

## 🔴 高風險文件（修改前必過 Smoke Test）

| 文件 | 影響功能 | 主要風險 |
|---|---|---|
| `app/api/v1/ingest.py` | 日記寫入、AI 解析、Task 自動建立 | 修改 Prompt 或 JSON 解析邏輯會導致資料寫入失敗 |
| `app/api/v1/memories.py` | 首頁 TodaySnapshot、Monthly Review | 修改查詢邏輯會導致前端無資料顯示 |
| `app/api/v1/chat.py` | CortexChat、RAG 對話 | 修改 system_prompt 或 RAG 注入會影響 AI 回應品質 |
| `app/core/gemini.py` | 所有 AI 功能的入口 | 修改 safe_generate_content 或 get_model 會導致全系統 AI 失效 |
| `app/core/database.py` | 所有 DB 寫入（safe_write） | 修改 safe_write 邏輯可能導致沉默的資料丟失 |
| `app/services/crystallizer.py` | 知識圖譜自動結晶 | 修改 prompt 或 nodes/edges 寫入邏輯 |

---

## ✅ 修改前的標準步驟

1. **確認後端在跑**：`uvicorn main:app --reload`
2. **跑 Smoke Test**（修改前）：
   ```bash
   python tools/smoke_test.py
   ```
   確認全部 `[OK]` 才開始修改。
3. **修改代碼**
4. **跑 Smoke Test**（修改後）：
   ```bash
   python tools/smoke_test.py
   ```
   全部 `[OK]` 才能 commit。

---

## 📋 Critical Function 清單

| 功能 | 進入點 | 後端路徑 | 期望回應 |
|---|---|---|---|
| 日記寫入 | CaptureView | `POST /api/v1/ingest` | `{"success": true, "data": {...}}` |
| 近期記憶 | TodaySnapshot | `GET /api/v1/memories/recent` | list of memories |
| 月度回顧 | Home → Monthly | `GET /api/v1/memories/monthly-review` | review text 非空 |
| RAG 對話 | CortexChat | `POST /api/v1/chat` | `{"response": "..."}` |
| 專案清單 | ProjectBoard | `GET /api/v1/projects/` | list of projects |
| 任務清單 | TaskList | `GET /api/v1/tasks/` | list of tasks |
| 系統狀態 | SystemStatus | `GET /api/v1/system/status` | `{"model": "..."}` |

---

## ⚠️ 已知的陷阱（修改時注意）

1. **ingest.py JSON 解析**：Gemini 不保證回傳合法 JSON，需要 regex 先提取 `{...}` 再 parse
2. **memories.py APIResponse**：`execute()` 回傳物件，必須取 `.data` 才是 list
3. **chat.py system_prompt**：Monthly Review 和 Growth Lessons 都在這裡注入，修改前後需驗證注入是否正常
4. **gemini.py safe_generate_content**：加入任何新的 except 分支都要確認不會吞掉非 429 的真正錯誤

---

**最後更新**: 2026-03-06 | **維護者**: 主開發 AI（依架構師方向更新）
