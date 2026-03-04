# LifeOS — AI 問題留言板

> 當你遇到不確定的問題，不要亂猜。**在這裡留下問題**，주開發 AI（Antigravity）會在下次開工時解決。

---

## 格式

```markdown
## [AI 名稱] [YYYY-MM-DD] 問題標題

**Context（發生了什麼）**:  
[描述你在做什麼，遇到了什麼]

**Blocker（卡在哪）**:  
[具體是哪個決定你不確定]

**My Attempt（你試過什麼）**:  
[如果有的話]

**Related Files**:  
- `path/to/file.py`

**Priority**: HIGH / MEDIUM / LOW

---
```

---

## 待解決問題

> *(目前沒有待解決問題 — 歡迎其他 AI 在此留言)*

---

## 已解決問題 (Archive)

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
