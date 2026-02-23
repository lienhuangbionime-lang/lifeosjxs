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
| `gemini-flash-lite-latest` | Ingest、基本 Chat |
| `gemini-2.5-flash` | 情境感知 Capture Prompts |
| `text-embedding-004` | 向量嵌入 (3072 dim) |

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

### Phase C: 短期記憶注入
- `chat.py` 中 `build_system_prompt()` 每次 Chat 注入 `evolution_log.json` 最後 5 筆
- AI 每次對話都帶著「最近發生了什麼」的上下文

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

### Model Names
- `sync_brain/SYSTEM_CONTEXT.md` 和 `SYSTEM_CONTEXT.md` 必須版本一致
- `soul_manager.py` 的 `drift_check()` 會比對版本號，不一致會 HALT

### 🚫 FATAL ERROR: Premature Documentation
- **NEVER** write a rule in `SYSTEM_CONTEXT` or commit a "fix" claiming it resolves an issue before actually testing it in the real application flow.
- A previous AI wrote a Regex fix for `ingest.py` and claimed success in Docs, but failed to realize the async Gemini call was broken, leading to silent failures and loss of user trust. **Verify first, Document second.**

---

## 🔄 開發工作流程

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

**最後更新**: 2026-02-24  
**狀態**: Phase B+C 完成 | Phase D (scoring_engine) 待實作
