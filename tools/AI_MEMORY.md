# LifeOS — AI 開發記憶

## 🎯 核心架構決策

### Embedding
- **維度**: 3072（`text-embedding-004`）
- **存放**: `memories.embedding VECTOR(3072)`
- **搜尋**: Supabase RPC `match_memories(query_embedding, match_threshold, match_count)`

### SDK
- ✅ `google.genai` (v1 API)
- ❌ `google.generativeai` (deprecated)
- 所有模型名必須通過 `app.core.gemini.sanitize_model_name()`

### 模型責任分工
| 模型 | 用途 |
|---|---|
| `gemini-3-pro-preview` | 深度思考、潛意識反思 |
| `gemini-flash-lite-latest` | Ingest、Crystallize、基本 Chat |
| `gemini-2.0-flash` | 最高速情境感知 (verified stable) |
| `text-embedding-004` | 向量嵌入 (3072 dim) |
| `BAAI/bge-reranker-v2-m3` | RAG 重排序 (HF Cross-Encoder) |

---

## 📋 已完成的重要決策

### Phase 13: 潛意識引擎
- 端點: `POST /api/v1/subconscious/reflect`
- 服務: `app/services/subconscious.py`
- 排程: APScheduler 每 12 小時自動執行
- 結果存回 `memories` 表（`type: "reflection"`）

### Phase 14: 情境感知 Capture
- 端點: `GET /api/v1/brain/contextual-prompts`
- 服務: `app/api/v1/crystallize.py`
- 模型: `gemini-2.5-flash`
- 讀取最近 48h 記憶 → 生成 3 個導引問句

### Phase B: AI 決策記錄
- 端點: `POST /api/v1/brain/growth/log-decision`
- 端點: `GET /api/v1/brain/growth/lessons`
- 表: `cortex_growth_logs`（AI 在 Glass Box 決策後必須呼叫）
- 前端: `cortex.brain.growth.logDecision()` / `.getLessons()`

### Phase 15: 知識結晶引擎 (Knowledge Crystallization)
- 端點: `GET /api/v1/brain/node/{label}/insight`
- 服務: `app/services/crystallizer.py`
- 腳本: `tools/bulk_crystallize.py`
- 功能: 自動從日記提取 Node (Entity) 與 Edge (Relationship) 並存入 `nodes`, `edges` 表。提供 AI 總結該節點在使用者生命中的意義。

### Phase C: 短期記憶注入
- `chat.py` 中 `build_system_prompt()` 每次 Chat 注入 `evolution_log.json` 最後 5 筆
- AI 每次對話都帶著「最近發生了什麼」的上下文

### Phase P6: Agent Skills Infrastructure
- **Orchestrator**: `app/services/skills.py` 實作動態解析 `skills/` 目錄。
- **動態注入**: 僅在檢測到關鍵字（如「反思」、「搜尋」）時注入完整 SKILL.md，降低 Token 浪費。

### Phase P8: Web Search Integration
- **服務**: `app/services/search.py` 使用 `duckduckgo-search`。
- **Tool**: 在 `chat.py` 註冊 `search_web_tool`。
- **協議**: `skills/research/SKILL.md` 指導 AI 在 RAG 失效時上網。

### Phase P10: Memory & Document Isolation
- **決策背景**: 外部資料（網頁、PDF）混入 `memories` 會稀釋使用者的真實日記，造成 RAG 檢索雜訊。
- **方案**: 啟用獨立的 `documents` 表。
- **規則**: 感性記憶歸 `memories`，硬性知識歸 `documents`。雙方在 `nodes` 表透過語義關聯。

---

## 🚨 已知問題 & 陷阱

### Windows 特有
- `print()` 不能有 emoji（UnicodeEncodeError）
- 檔案 I/O 必須加 `encoding="utf-8"`
- `&&` 在 PowerShell 不能用，改用 `;`

### Python Regex CJK Pitfalls
- `\b` (word boundary) in Python regex **fails** when English/Numbers are adjacent to CJK characters (e.g., `2/1日記`).
- **Fix**: Use lookarounds `(?<!\d)` and `(?!\d)` instead of `\b` when extracting dates/numbers from mixed-language text.

### LLM Formatting Non-Determinism
- Never assume the LLM will strictly follow markup formatting (e.g. `[YYYY-MM-DD]`). Sometimes it drops brackets: `YYYY-MM-DD`.
- Regex replacing AI-generated markdown must possess ultra-permissive structures (e.g. `\[?` optional brackets) so fixes aren't silently skipped.

### Supabase
- RPC `match_memories` 需要先執行 `migrations/006_match_memories_rpc.sql`
- `memories.date` 是 UNIQUE KEY（同一天只有一筆，用 upsert）

### Model Names & 404 Traps
- **Trap**: 直接在程式碼寫 `gemini-1.5-flash` 可能導致 404，因為 SDK v1beta 可能不支援。
- **Fix**: 必須使用 `app.core.gemini.get_model("fast")` 或 `get_model("smart")` 來獲取已經經過 `sanitize_model_name()` 處理過的正確 ID。
- 模型版本號必須與 `soul_manager.py` 的 `drift_check()` 保持同步。

### 🚫 FATAL ERROR: Windows Encoding & Emojis
- **Problem**: Windows (cp950) 終端機對 Emoji 極度敏感，會導致 Python 程序崩潰 (UnicodeEncodeError)。
- **Rule**: 所有正式代碼、測試腳本、print() logs 絕對禁止出現 Emoji。

### 🚫 FATAL ERROR: Premature Documentation
- **NEVER** write a rule in `SYSTEM_CONTEXT` or commit a "fix" claiming it resolves an issue before actually testing it in the real application flow.
- A previous AI wrote a Regex fix for `ingest.py` and claimed success in Docs, but failed to realize the async Gemini call was broken, leading to silent failures and loss of user trust. **Verify first, Document second.**

### 🚫 FATAL ERROR: API Namespace Refactor Must Be Global

- **Date**: 2026-02-25
- **Mistake**: When refactoring API methods from `cortex.updateProject()` to `cortex.projects.update()`,
  I only updated the **file I was directly editing** (`ProjectBoard.tsx`). I forgot `useProjectSync.ts`
  also used the old API, causing a build failure.
- **Rule**: **After any API rename/namespace change, ALWAYS run a global search before committing:**
  ```bash
  # Search for ALL usages of old API names before committing
  grep -r "cortex\.updateProject\|cortex\.deleteProject\|cortex\.mergeProject\|cortex\.createProject" frontend-body/
  ```
- **Root cause**: I did not treat the refactor as a cross-codebase change.

---

### 🚫 FATAL ERROR: FastAPI `request` vs `payload` Confusion

- **Date**: 2026-02-25
- **Mistake**: In `chat.py`, the function signature is `stream_chat(request: Request, payload: ChatRequest)`.
  When I added new code inside the function, I kept writing `request.message`, `request.history`,
  `request.url_context` — but `request` is the **HTTP Request object** (used only for headers like 
  Gemini API key). The JSON body lives on `payload`.
- **Rule**: In FastAPI endpoints with both `request: Request` and a Pydantic `payload`:
  - `request` → **HTTP/headers only** (use `request.headers.get(...)`)
  - `payload` → **JSON body fields** (`.message`, `.history`, `.model`, etc.)

---



```bash
# 開始前
1. 讀 sync_brain/evolution_log.json 最後 5 筆
2. 讀 sync_brain/registry.json 確認 schema

# 開發中
3. 修改 backend-cortex/app/（系統 AI 領域）
4. 工具腳本放在 tools/
5. 重要文件放在 sync_brain/

# 完成後
6. git commit
7. 追加 sync_brain/evolution_log.json
8. 更新這個文件（AI_MEMORY.md）
```

---

**最後更新**: 2026-02-27  
**狀態**: v3.7.6 完成（技能引擎 + Web Search 開通）| 下一步: Phase P10 Isolation Engineering
