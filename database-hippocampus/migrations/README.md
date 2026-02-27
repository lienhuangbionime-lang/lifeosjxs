# Database Migrations (演化紀錄簿)

本目錄存放所有曾經執行於 Supabase / PostgreSQL 的 SQL 腳本，紀錄了從 v1.0 到 v3.8.x 的記憶演化史。

---

## 🛠️ 如何執行 Migrations

### 選項 1：Supabase SQL Editor (最推薦)
1. 進入 [Supabase Dashboard](https://app.supabase.com/)。
2. 點擊 **SQL Editor**。
3. 貼上腳本內容（例如 `007_init_documents_table.sql`）。
4. 點擊 **Run**。

### 選項 2：Supabase CLI
```bash
cd database-hippocampus
supabase db push
```

---

## 📋 關鍵 Migration 說明

1. **`supabase_init.sql`**: 核心基礎設施（UUID, pgvector, memories 表）。
2. **`002_sync_supabase_v3.5.sql`**: 結構修補與 GIN Index 強化。
3. **`003_add_monthly_review_table.sql`**: 建立月度回顧表。
4. **`007_init_documents_table.sql`**: 建立外部文獻隔離層 (Documents Table)。

---

## 🧬 當前基準架構 (v3.8.1 Ground Truth)

在執行完所有 Migrations 後，核心表 `memories` 應具備以下特徵：
- **Forensic Data**: `local_path`, `content_hash`, `ai_insights` (v3.8 新增)。
- **Vector Engine**: `embedding` VECTOR(3072)。
- **Metadata**: `tags` TEXT[], `category` TEXT。

---
**注意**：執行任何 Migration 前，務必先手動備份 `sync_brain/registry.json`，並確保在開發環境測試通過。
