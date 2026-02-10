# 🚀 LifeOS 資料庫快速重置指南

## 立即執行（3 分鐘解決）

### Step 1: 前往 Supabase Dashboard
1. 打開瀏覽器
2. 前往：https://supabase.com/dashboard
3. 選擇您的專案

### Step 2: 打開 SQL Editor
1. 左側選單 → **SQL Editor**
2. 點擊 **New query**

### Step 3: 執行重置腳本
1. 複製 `backend-cortex/infra/supabase_reset_and_init.sql` 的**完整內容**
2. 貼到 SQL Editor
3. 點擊 **Run** (或按 Ctrl+Enter)
4. 等待執行完成（約 5-10 秒）

### Step 4: 驗證結果
在 Supabase Dashboard 左側選單：
- **Table Editor** → 應該看到 5 個表：
  - ✅ memories
  - ✅ projects
  - ✅ tasks
  - ✅ nodes
  - ✅ edges

### Step 5: 測試存檔功能
1. 回到 LifeOS 前端
2. 寫一篇測試日記
3. 點擊 **INGEST & ANALYZE**
4. 點擊 **SAVE TO BRAIN**
5. 切換到 **Brain** 或 **List** 視圖
6. 應該能看到您的日記！

---

## 如果看到重複的表？

### 方案 A：使用重置腳本（推薦）
執行 `supabase_reset_and_init.sql` 會**自動清理**所有舊表，然後重建乾淨的結構。

### 方案 B：手動刪除（不推薦）
1. 在 Table Editor 中
2. 對每個重複的表點擊 **...** → **Delete table**
3. 然後執行重置腳本

---

## 未來如何避免混亂？

### 原則 1：只執行一個腳本
- ✅ 使用：`supabase_reset_and_init.sql`
- ❌ 不要：手動創建表或執行多個腳本

### 原則 2：需要新功能時
1. 先閱讀 `docs/DATABASE_EVOLUTION_GUIDE.md`
2. 使用決策樹判斷方法
3. 創建新的遷移腳本（放在 `migrations/` 目錄）

### 原則 3：定期備份
- Supabase 自動備份（Dashboard → Database → Backups）
- 每週手動導出一次（可選）

---

## 常見問題

### Q: 執行腳本會刪除我的數據嗎？
**A:** 是的，`supabase_reset_and_init.sql` 會清空所有表。如果您有重要數據，請先備份。

### Q: 如何備份數據？
**A:** 
1. Supabase Dashboard → Database → Backups
2. 或使用 SQL Editor 執行：
```sql
SELECT * FROM memories; -- 複製結果
```

### Q: 我想新增一個「睡眠品質」指標，怎麼做？
**A:** 閱讀 `docs/DATABASE_EVOLUTION_GUIDE.md` 的「情境 1」，使用 JSONB 快速實現。

---

## 緊急聯絡

如果遇到問題：
1. 檢查後端日誌（terminal 輸出）
2. 檢查 Supabase Logs（Dashboard → Logs）
3. 詢問 AI：「我的資料庫出現 XXX 錯誤」

**記住：資料庫可以重置，代碼可以修改，但您的想法和系統才是最寶貴的。**
