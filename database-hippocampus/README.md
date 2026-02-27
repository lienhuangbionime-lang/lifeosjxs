# database-hippocampus (Memory Management Layer)

> **定位**：LifeOS 的「海馬迴」— 負責定義記憶的結構 DNA 與演化規律。

雖然 LifeOS 的後端調度引擎 (`backend-cortex`) 目前是透過動態 SDK 運作，但本目錄提供了系統的**靜態真理定義**，是系統穩定性的最後一道防線。

---

## 📋 核心組成

### 1. 🧬 數據基因圖譜 (`prisma/schema.prisma`)
*   **用途**：定義所有 Table（memories, projects, tasks...）的資料型別、關聯與預設值。
*   **價值**：作為 AI 理解數據結構的「唯一技術規格書」。當需要變更資料庫結構時，此檔案應優先被更新。

### 2. ⏳ 演化紀錄簿 (`migrations/`)
*   **用途**：存放執行於 Supabase / PostgreSQL 的 SQL 腳本。
*   **內容**：
    *   `007_init_documents_table.sql`: 建立文件隔離層。
    *   `003_add_monthly_review_table.sql`: 初始化回顧系統。
    *   `001_add_v7_fields.sql`: 歷史結構升級存檔。
*   **價值**：確保系統具備「災難還原」與「環境克隆」的能力。

---

## 🛠️ 開發與維護指南

### 什麼時候需要動這裡？
1.  **新增功能**：當你需要 AI 紀錄新的數據類型時（例如：睡眠數據、財務標籤）。
2.  **架構優化**：當你需要優化檢索效能（例如：增加 SQL Index）時。
3.  **環境遷移**：當你需要將 LifeOS 部署到新的 Supabase 帳號時。

### 🚨 重要禁忌
*   **維度一致性**：所有 Embedding 欄位（雖然 Prisma 未完全標註）必須維持 **3072 維** (`gemini-embedding-001`)。
*   **對齊檢查**：修改此處後，務必同步更新 `backend-cortex/schemas/registry.json`，確保 AI 的「靜態認知」與「動態註冊表」一致。

---
**版本**: v3.8.1 "Cortex"
**狀態**: 已完成絕對對齊 | **角色**: 靜態藍圖與演化紀錄
