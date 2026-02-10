# 🤖 AI 協作式 Schema 演進 - 使用指南

## 系統已就緒！

我已經為您建立了完整的 AI 協作式資料庫演進系統。現在您可以用自然語言告訴我您想追蹤什麼，我會自動分析並提供建議。

---

## 🚀 快速開始

### 範例 1：追蹤睡眠品質

**您說：**
> "我想追蹤睡眠品質"

**AI 回應：**
```
我分析了您的需求，這是一個簡單的數值指標。

【方案 A】使用 JSONB metadata（推薦快速驗證）
- 複雜度：★☆☆☆☆
- 效能：★★★☆☆
- 需要遷移：否
- 實現時間：< 1 分鐘
- 優點：立即可用、無需遷移、靈活
- 缺點：查詢效能較低、無法建立索引

【方案 B】新增專用欄位 sleep_quality
- 複雜度：★★★☆☆
- 效能：★★★★★
- 需要遷移：是
- 實現時間：5 分鐘
- 優點：查詢效能高、可建立索引、類型安全
- 缺點：需要資料庫遷移、結構變更

您想選擇哪個方案？（輸入 A 或 B）
```

**您選擇：** A

**AI 執行：**
```
✅ 已更新 SorterAgent 提示詞
✅ 已更新 API Schema
✅ 已更新前端輸入組件

現在您可以在日記中寫「睡眠品質 8/10」，AI 會自動提取並存入 metadata。

30 天後，如果您覺得有用，我可以幫您升級為專用欄位（方案 B）。
```

---

## 📋 支持的需求類型

### 1. 簡單數值指標
**關鍵詞：** 品質、分數、評分、指標、等級

**範例：**
- "我想追蹤睡眠品質"
- "我想記錄每天的壓力指數"
- "我想評估工作滿意度"

**AI 建議：** JSONB → 專用欄位

---

### 2. 複雜追蹤系統
**關鍵詞：** 記錄、追蹤、日誌、清單

**範例：**
- "我想追蹤每天的運動記錄"
- "我想記錄閱讀的書籍"
- "我想追蹤飲食日誌"

**AI 建議：** JSONB 陣列 → 關聯表

---

### 3. 布林標記
**關鍵詞：** 是否、有沒有、開關

**範例：**
- "我想標記是否做夢"
- "我想記錄有沒有運動"
- "我想追蹤是否冥想"

**AI 建議：** 直接新增 BOOLEAN 欄位

---

## 🛠️ 工作流程

### Step 1: 提出需求
```
User: "我想追蹤 X"
```

### Step 2: AI 分析
```
AI 自動：
1. 讀取 schemas/registry.json
2. 分析需求類型
3. 檢查是否已有類似欄位
4. 生成 2-3 個方案
```

### Step 3: 用戶選擇
```
User: "選擇方案 B"
```

### Step 4: AI 執行
```
AI 自動：
1. 生成 SQL 遷移腳本
2. 更新 Python Pydantic models
3. 更新 API 路由
4. 更新前端組件
5. 執行測試
6. 記錄到 evolution_log.json
```

### Step 5: 驗證
```
User: 測試新功能
AI: 監控使用情況，30 天後建議優化
```

---

## 📁 系統文件

### 核心文件
- **`schemas/registry.json`** - 當前資料庫結構定義
- **`schemas/evolution_log.json`** - 演進歷史記錄
- **`tools/schema_assistant.py`** - AI 使用的分析工具

### 文檔
- **`docs/AI_SCHEMA_EVOLUTION_PROTOCOL.md`** - 完整協議
- **`docs/DATABASE_EVOLUTION_GUIDE.md`** - 演進策略指南
- **`docs/DATABASE_QUICK_RESET.md`** - 快速重置指南

### 遷移腳本
- **`migrations/001_initial_schema.sql`** - 初始 schema
- **`migrations/002_add_xxx.sql`** - 未來的遷移（自動生成）

---

## 🎯 實際案例

### 案例 1：睡眠追蹤（已測試）

**需求：** "我想追蹤睡眠品質"

**AI 分析結果：**
```json
{
  "detected_type": "simple_numeric",
  "suggestions": [
    {
      "option": "A",
      "method": "JSONB metadata",
      "complexity": 1,
      "migration_required": false
    },
    {
      "option": "B",
      "method": "New column",
      "complexity": 3,
      "migration_required": true
    }
  ]
}
```

**生成的 SQL（方案 B）：**
```sql
-- Migration 002: Add sleep_quality to memories
BEGIN;

ALTER TABLE public.memories
ADD COLUMN IF NOT EXISTS sleep_quality INT
DEFAULT 5
CHECK (sleep_quality >= 0 AND sleep_quality <= 10);

CREATE INDEX IF NOT EXISTS idx_memories_sleep_quality
ON public.memories(sleep_quality);

COMMIT;
```

---

## 🔄 未來優化流程

### 30 天後
```
AI: 我注意到您在過去 30 天使用了 sleep_quality 共 28 次。
    目前它存在 metadata 中，查詢效能為 3/5。
    
    建議升級為專用欄位以提升效能到 5/5。
    
    是否執行升級？

User: "是"

AI: [自動執行遷移]
    ✅ 已創建 sleep_quality 欄位
    ✅ 已遷移歷史數據
    ✅ 已更新索引
    ✅ 效能提升 67%
```

---

## 🚨 安全機制

### 1. 遷移前檢查
- ✅ 自動備份
- ✅ 語法驗證
- ✅ 影響範圍分析
- ✅ 回滾腳本生成

### 2. 用戶確認
```
AI: 這是遷移預覽：
    
    [顯示 SQL]
    
    影響範圍：
    - 修改表：memories
    - 新增欄位：sleep_quality
    - 預計執行時間：< 1 秒
    - 可回滾：是
    
    輸入 "CONFIRM" 執行
```

### 3. 執行後驗證
- ✅ 數據完整性檢查
- ✅ 性能測試
- ✅ 自動回滾（如果失敗）

---

## 💡 最佳實踐

### 1. 先實驗，後固化
```
Week 1-4:  使用 JSONB（快速驗證）
Week 5:    AI 建議升級
Week 6+:   使用專用欄位（優化效能）
```

### 2. 定期審查
```
每季度：
- AI 分析 metadata 使用情況
- 提出優化建議
- 清理未使用的欄位
```

### 3. 文檔化決策
```
每次變更：
- 自動記錄到 evolution_log.json
- 生成遷移腳本到 migrations/
- 更新 registry.json
```

---

## 🎓 進階用法

### 手動觸發分析
```python
from tools.schema_assistant import suggest_schema_change

result = suggest_schema_change("我想追蹤運動記錄")
print(result)
```

### 手動生成遷移
```python
from tools.schema_assistant import generate_migration

sql = generate_migration(
    table="memories",
    column_name="exercise_duration",
    column_type="INT",
    default_value="0"
)
print(sql)
```

---

## 📞 需要幫助？

### 常見問題

**Q: 如何查看當前 schema？**
A: 查看 `schemas/registry.json`

**Q: 如何回滾遷移？**
A: 每個遷移腳本都包含回滾 SQL

**Q: AI 如何知道我的需求？**
A: 使用自然語言描述，AI 會分析關鍵詞並查詢 registry.json

**Q: 可以同時追蹤多個指標嗎？**
A: 可以！一次一個，或者告訴我「我想追蹤 A、B、C」

---

## 🚀 現在就試試！

**告訴我：**
- "我想追蹤 ___"
- "我想記錄 ___"
- "我想新增 ___ 功能"

**我會：**
1. 分析您的需求
2. 提供 2-3 個方案
3. 生成遷移腳本
4. 執行並驗證
5. 記錄演進歷史

**讓我們一起打造您的個人化 LifeOS！** 🎉
