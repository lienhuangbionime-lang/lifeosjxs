# LifeOS 資料庫擴展指南

## 🎯 設計哲學

LifeOS 的資料庫設計遵循 **「穩定核心 + 彈性擴展」** 原則：

- **核心表（不變）**：`memories`, `projects`, `tasks`
- **擴展方式**：透過 `JSONB` 欄位和新表來適應變化

---

## 📊 當前架構總覽

### 核心表
1. **memories** - 日記與記憶（核心數據）
2. **projects** - 專案管理
3. **tasks** - 任務清單
4. **nodes** - 知識圖譜節點
5. **edges** - 知識圖譜連線

### 關鍵設計決策
- ✅ 使用 `JSONB` 的 `metadata` 欄位來存儲未來的自定義屬性
- ✅ 使用 `TEXT[]` 的 `tags` 來支持動態標籤
- ✅ 使用 `CHECK` 約束來確保數據完整性
- ✅ 使用觸發器自動更新 `updated_at`

---

## 🚀 如何新增評估標準

### 情境 1：新增簡單的數值指標（例如：睡眠品質）

**方法 A：使用現有的 JSONB（推薦，快速）**

```sql
-- 不需要修改表結構！直接在應用層寫入
-- 後端代碼示例：
data = {
    "date": "2026-02-11",
    "content": "今天睡得很好",
    "mood": 8,
    "focus": 7,
    "energy": 9,
    "tags": ["sleep", "health"],
    "category": "Health",
    -- 新增自定義指標到 metadata
    "metadata": {
        "sleep_quality": 9,
        "sleep_hours": 8.5,
        "dream_recall": true
    }
}
```

**方法 B：新增專用欄位（如果需要索引和查詢優化）**

```sql
-- 1. 新增欄位
ALTER TABLE public.memories 
ADD COLUMN sleep_quality INT DEFAULT 5 CHECK (sleep_quality >= 0 AND sleep_quality <= 10);

-- 2. 創建索引（如果需要頻繁查詢）
CREATE INDEX idx_memories_sleep_quality ON public.memories(sleep_quality);

-- 3. 更新後端 Schema（app/models/schemas.py）
class LogEntrySchema(BaseModel):
    # ... 現有欄位 ...
    sleep_quality: Optional[int] = 5
```

---

### 情境 2：新增複雜的追蹤系統（例如：習慣追蹤）

**推薦方式：創建關聯表**

```sql
-- 1. 創建習慣定義表
CREATE TABLE public.habit_definitions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    category TEXT,
    target_frequency TEXT, -- 'daily', 'weekly', 'monthly'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 創建習慣記錄表（與 memories 關聯）
CREATE TABLE public.habit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    memory_id UUID REFERENCES public.memories(id) ON DELETE CASCADE,
    habit_id UUID REFERENCES public.habit_definitions(id) ON DELETE CASCADE,
    completed BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(memory_id, habit_id) -- 防止重複記錄
);

-- 3. 創建索引
CREATE INDEX idx_habit_logs_memory ON public.habit_logs(memory_id);
CREATE INDEX idx_habit_logs_habit ON public.habit_logs(habit_id);
```

---

### 情境 3：新增時間序列數據（例如：體重追蹤）

```sql
CREATE TABLE public.metrics_timeseries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    metric_name TEXT NOT NULL, -- 'weight', 'blood_pressure', etc.
    value FLOAT NOT NULL,
    unit TEXT, -- 'kg', 'mmHg', etc.
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    memory_id UUID REFERENCES public.memories(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_metrics_name_time ON public.metrics_timeseries(metric_name, recorded_at DESC);
```

---

## 🔄 資料遷移策略

### 原則
1. **永遠不要直接刪除欄位** - 先標記為 deprecated，觀察 30 天後再移除
2. **使用遷移腳本** - 所有結構變更都要有對應的 `.sql` 文件
3. **保持向後兼容** - 新欄位必須有 DEFAULT 值

### 遷移腳本範例

```sql
-- migrations/2026_02_11_add_sleep_tracking.sql

BEGIN;

-- 1. 新增欄位
ALTER TABLE public.memories 
ADD COLUMN IF NOT EXISTS sleep_quality INT DEFAULT 5 
CHECK (sleep_quality >= 0 AND sleep_quality <= 10);

-- 2. 回填歷史數據（如果需要）
UPDATE public.memories 
SET sleep_quality = 5 
WHERE sleep_quality IS NULL;

-- 3. 創建索引
CREATE INDEX IF NOT EXISTS idx_memories_sleep_quality 
ON public.memories(sleep_quality);

COMMIT;
```

---

## 🛡️ 應對快速變化的策略

### 1. **使用 JSONB 作為緩衝區**
```sql
-- 所有新的、不確定的指標先放到 metadata
UPDATE memories SET metadata = metadata || '{"new_metric": 123}'::jsonb;

-- 等確定後再提升為專用欄位
ALTER TABLE memories ADD COLUMN new_metric INT;
UPDATE memories SET new_metric = (metadata->>'new_metric')::int;
```

### 2. **版本化你的 Schema**
```sql
-- 在 metadata 中記錄 schema 版本
{
  "schema_version": "3.5",
  "custom_fields": {
    "experimental_metric": 42
  }
}
```

### 3. **建立實驗表**
```sql
-- 用於測試新功能，不影響核心表
CREATE TABLE public.experiments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    experiment_name TEXT NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 📋 快速決策樹

```
需要新增評估標準？
│
├─ 是簡單的數值（1-2個欄位）？
│  ├─ 是 → 使用 JSONB metadata（快速）
│  └─ 否 → 繼續
│
├─ 需要頻繁查詢/聚合？
│  ├─ 是 → 新增專用欄位 + 索引
│  └─ 否 → 使用 JSONB
│
├─ 是複雜的關聯數據（如習慣、標籤）？
│  └─ 是 → 創建新的關聯表
│
└─ 還在實驗階段？
   └─ 是 → 使用 experiments 表或 JSONB
```

---

## 🎓 最佳實踐

1. **先用 JSONB，後提升為欄位**
   - 快速驗證想法
   - 確定有價值後再優化

2. **保持 `memories` 表簡潔**
   - 核心指標：mood, focus, energy
   - 其他都用關聯表或 JSONB

3. **定期審查 metadata**
   - 每季度檢查 JSONB 中的常用欄位
   - 提升為專用欄位以提升性能

4. **文檔化所有變更**
   - 在 `migrations/` 目錄記錄每次變更
   - 在代碼中註釋為什麼這樣設計

---

## 🚨 緊急應變方案

### 如果資料庫結構完全混亂了？

1. **執行 `supabase_reset_and_init.sql`**
   - 清空所有表
   - 重建乾淨的結構

2. **從備份恢復數據**
   - Supabase 自動備份（Dashboard → Database → Backups）
   - 或使用 `pg_dump` 手動備份

3. **重新思考架構**
   - 回到這份文檔
   - 使用決策樹重新設計

---

## 📞 需要幫助時

1. 查看此文檔的決策樹
2. 檢查 `migrations/` 目錄的歷史範例
3. 詢問 AI：「我想追蹤 X，應該用什麼方式？」

記住：**沒有完美的架構，只有適合當下的架構。保持靈活，持續演進。**
