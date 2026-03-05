# LifeOS — AI 跨角色問題留言板 (QUESTIONS.md)

> **這是 AI 之間的異步通訊頻道。**
> 任何 AI 遇到需要跨角色決定的問題，在此留言，不要亂猜。

---

## 📬 通訊路由標籤格式

| 標籤 | 說明 |
|---|---|
| `[FLASH→PRO]` | Flash 工程師 → Gemini Pro 任務管家（技術細節問題） |
| `[PRO→CLAUDE]` | Gemini Pro → Claude 架構師（架構決策問題） |
| `[CLAUDE→ALL]` | Claude → 所有 AI（架構決定公告） |
| `[FLASH→CLAUDE]` | Flash → Claude（緊急架構問題，跳過 Pro） |

---

## 問題模板

```markdown
## [路由標籤] [YYYY-MM-DD] 問題標題

**Context（發生了什麼）**:
[描述你在做什麼，遇到了什麼]

**Blocker（卡在哪）**:
[具體是哪個決定你不確定]

**My Attempt（你試過什麼）**:
[如果有的話]

**Related Files**:
- `path/to/file.py`

**Priority**: HIGH / MEDIUM / LOW
```

---

## 📥 待解決問題

> *(目前沒有待解決問題)*

---

## ✅ 已解決問題 (Archive)

### [Antigravity] 2026-02-24 pgvector HNSW 無法建立在 3072 維度

**Context**: 建立 `cortex_growth_logs` embedding index 時報錯
**Blocker**: `ERROR: 54000: column cannot have more than 2000 dimensions for hnsw index`
**Solution**: 移除 HNSW index，改用 exact cosine search（cortex_growth_logs 資料量小，效能足夠）
**File**: `backend-cortex/infra/006_growth_logs_embedding.sql`

---

### [Antigravity] 2026-02-24 ingest.py 使用舊版 SDK

**Context**: `ingest.py` 使用 `import google.generativeai as genai`（deprecated）
**Solution**: 改用 `gemini_client.models.generate_content(model, contents)` via `app.core.gemini`
**File**: `backend-cortex/app/api/v1/ingest.py:253`
