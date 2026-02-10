# 🎯 LifeOS v3.5 - 立即行動清單

## 當前狀態

### ✅ 已完成
- [x] Context Engineering 基礎設施
  - SYSTEM_CONTEXT.md (完整系統上下文)
  - .cursorrules (Cursor IDE 配置)
  - schemas/registry.json (資料庫結構定義)
  - schemas/evolution_log.json (演進歷史)
  - tools/schema_assistant.py (AI 分析工具)

- [x] 文檔系統
  - AI_SCHEMA_EVOLUTION_PROTOCOL.md
  - CONTEXT_ENGINEERING_GUIDE.md
  - DATABASE_EVOLUTION_GUIDE.md
  - TESTING_GUIDE.md

- [x] 測試工具
  - test_system_integration.py (完整系統測試)

- [x] 後端運行中
  - FastAPI 運行在 http://0.0.0.0:8000
  - 所有 emoji 已移除（Windows 兼容）

### ⚠️ 待處理
- [ ] **Supabase 資料庫初始化**（最優先）
- [ ] 前端測試
- [ ] 完整系統測試

---

## 🚨 立即執行（5 分鐘）

### Step 1: 初始化 Supabase 資料庫

1. **打開瀏覽器**
   - 前往：https://supabase.com/dashboard
   - 登入您的帳號
   - 選擇您的專案

2. **執行 SQL 腳本**
   - 左側選單 → **SQL Editor**
   - 點擊 **New query**
   - 複製以下文件的完整內容：
     ```
     backend-cortex/infra/supabase_reset_and_init.sql
     ```
   - 貼到 SQL Editor
   - 點擊 **Run** (或按 Ctrl+Enter)

3. **驗證結果**
   - 左側選單 → **Table Editor**
   - 應該看到 5 個表：
     - ✅ memories
     - ✅ projects
     - ✅ tasks
     - ✅ nodes
     - ✅ edges

### Step 2: 執行系統測試

```bash
python test_system_integration.py
```

**預期結果**:
```
[OK] Backend Health
[OK] Supabase Connection
[OK] AI Analysis
[OK] Save to Database
[OK] Retrieve Memories
[OK] All API Endpoints
[OK] Schema Registry

[SUCCESS] All tests passed! System is ready.
```

### Step 3: 測試前端

```bash
cd frontend-body
npm run dev
```

然後打開 http://localhost:3000

**測試流程**:
1. 在 Capture 輸入日記
2. 點擊 "INGEST & ANALYZE"
3. 等待 AI 分析
4. 點擊 "SAVE TO BRAIN"
5. 切換到 Brain 分頁查看圖譜
6. 切換到 List 分頁查看列表

---

## 📚 重要文件說明

### 對於 AI 開發（優先級排序）

1. **`SYSTEM_CONTEXT.md`** ⭐⭐⭐⭐⭐
   - **最重要的文件**
   - 完整的系統真相來源
   - AI 的「員工手冊」
   - 包含所有架構決策、技術棧、規範

2. **`.cursorrules`** ⭐⭐⭐⭐
   - Cursor IDE 專用配置
   - 快速參考規則
   - **指向** SYSTEM_CONTEXT.md

3. **`schemas/registry.json`** ⭐⭐⭐⭐
   - 資料庫結構定義（AI 可讀）
   - Schema 演進的基礎
   - 動態更新

### 關係圖
```
當 AI 要寫代碼時：
1. 先讀 .cursorrules (快速檢查)
2. 然後讀 SYSTEM_CONTEXT.md (完整上下文)
3. 如果涉及資料庫，讀 schemas/registry.json
4. 如果需要演進，使用 tools/schema_assistant.py
```

### 對於人類開發者

1. **`docs/TESTING_GUIDE.md`** - 完整測試指南
2. **`docs/CONTEXT_ENGINEERING_GUIDE.md`** - AI 協作指南
3. **`docs/DATABASE_EVOLUTION_GUIDE.md`** - 資料庫演進策略
4. **`docs/AI_SCHEMA_USAGE_GUIDE.md`** - Schema 變更使用指南

---

## 🎓 未來開發工作流程

### 當您想新增功能時

**範例：「我想追蹤睡眠品質」**

```
You: "我想追蹤睡眠品質"

AI: [自動讀取 SYSTEM_CONTEXT.md]
    [自動讀取 schemas/registry.json]
    [使用 tools/schema_assistant.py 分析]
    
    "我分析了您的需求，這是簡單數值指標。
     
     方案 A: JSONB metadata (快速驗證)
     - 立即可用，無需遷移
     
     方案 B: 新增專用欄位 (優化效能)
     - 需要遷移，更好的查詢性能
     
     建議先用 A 驗證 30 天，再升級為 B。
     您選擇哪個？"

You: "選 A"

AI: [自動執行]
    ✅ 更新 SorterAgent 提示詞
    ✅ 更新 API Schema
    ✅ 更新前端組件
    ✅ 記錄到 evolution_log.json
    
    "完成！現在可以使用了。"
```

### 當 AI 犯錯時

```
1. 不要只修代碼
2. 分析根本原因
3. 更新 SYSTEM_CONTEXT.md
4. 新增對應規則
5. 下次 AI 就不會再犯
```

---

## 💡 關鍵洞察

### Q: `.cursorrules` 是最重要的文件嗎？

**A: 不完全是。**

**重要性排序**:
1. **SYSTEM_CONTEXT.md** (最重要) - 完整真相
2. **.cursorrules** (快速參考) - 指向 SYSTEM_CONTEXT.md
3. **schemas/registry.json** (動態知識) - 資料庫結構

**比喻**:
- `SYSTEM_CONTEXT.md` = 完整的員工手冊（500 頁）
- `.cursorrules` = 快速參考卡（1 頁）
- `schemas/registry.json` = 即時更新的組織架構圖

**使用方式**:
- Cursor IDE 會自動讀取 `.cursorrules`
- `.cursorrules` 告訴 AI：「去讀 SYSTEM_CONTEXT.md」
- AI 讀取完整上下文後，再寫代碼

---

## 🎯 成功標準

### 系統測試通過
- ✅ 所有 7 項測試通過
- ✅ 可以存檔日記
- ✅ 可以查看 Brain 圖譜
- ✅ 可以查看 List 列表

### AI 協作成功
- ✅ AI 在寫代碼前讀取 SYSTEM_CONTEXT.md
- ✅ AI 遵循所有禁止事項
- ✅ AI 遵循所有必須實踐
- ✅ 代碼準確率 ≥ 90%

### Schema 演進成功
- ✅ 可以用自然語言描述需求
- ✅ AI 自動分析並提供方案
- ✅ 用戶確認後自動執行
- ✅ 所有變更都有記錄

---

## 🚀 現在就開始！

### 1. 初始化資料庫（最優先）
前往 Supabase Dashboard，執行 `supabase_reset_and_init.sql`

### 2. 執行系統測試
```bash
python test_system_integration.py
```

### 3. 測試前端
```bash
cd frontend-body
npm run dev
```

### 4. 開始使用
寫一篇日記，體驗完整流程！

---

## 📞 需要幫助？

### 測試失敗
查看 `docs/TESTING_GUIDE.md` 的「常見問題排查」

### AI 寫錯代碼
更新 `SYSTEM_CONTEXT.md`，新增對應規則

### 想新增功能
告訴 AI：「我想追蹤 XXX」，AI 會自動分析並提供方案

---

**您已經擁有完整的 Context Engineering 基礎設施！**

**從「開發者」進化為「AI 系統架構師」的旅程，現在開始！** 🚀
