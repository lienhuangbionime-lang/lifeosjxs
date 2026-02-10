# LifeOS Schema Evolution Protocol

## 系統架構

```
User Request → AI Analysis → Generate Migration → User Approval → Execute → Update Docs
```

## 核心組件

### 1. Schema Registry (schemas/registry.json)
記錄當前的資料庫結構和演進歷史

### 2. Migration Generator (tools/migration_generator.py)
AI 使用此工具生成遷移腳本

### 3. Migration Executor (tools/migration_executor.py)
執行經過批准的遷移腳本

### 4. Schema Validator (tools/schema_validator.py)
驗證遷移腳本的安全性

---

## AI 工作流程

### Step 1: 理解需求
```
User: "我想追蹤睡眠品質"
AI: 分析 schemas/registry.json，判斷最佳方案
```

### Step 2: 生成建議
```
AI 提出 3 個選項：
A. 使用 JSONB metadata (快速，無需遷移)
B. 新增 sleep_quality 欄位 (需要遷移，更好的查詢性能)
C. 創建 sleep_logs 關聯表 (複雜追蹤)
```

### Step 3: 用戶確認
```
User: "選擇 B"
AI: 生成遷移腳本並顯示預覽
User: "執行"
```

### Step 4: 自動執行
```
AI:
1. 生成 SQL 遷移腳本
2. 更新 Python Schema (Pydantic models)
3. 更新 API 路由
4. 更新文檔
5. 執行測試
```

---

## 文件結構

```
backend-cortex/
├── schemas/
│   ├── registry.json          # 當前 schema 定義
│   ├── evolution_log.json     # 演進歷史
│   └── models/
│       ├── memory.py          # Pydantic models
│       ├── project.py
│       └── task.py
├── migrations/
│   ├── 001_initial_schema.sql
│   ├── 002_add_sleep_quality.sql
│   └── ...
└── tools/
    ├── migration_generator.py
    ├── migration_executor.py
    └── schema_validator.py
```

---

## 實現細節

### schemas/registry.json
```json
{
  "version": "3.5",
  "last_updated": "2026-02-11T03:16:19+08:00",
  "tables": {
    "memories": {
      "columns": {
        "id": {"type": "UUID", "primary_key": true},
        "content": {"type": "TEXT", "nullable": false},
        "date": {"type": "DATE", "nullable": false},
        "mood": {"type": "INT", "default": 5, "check": "0-10"},
        "focus": {"type": "INT", "default": 5, "check": "0-10"},
        "energy": {"type": "INT", "default": 5, "check": "0-10"},
        "tags": {"type": "TEXT[]", "default": []},
        "metadata": {"type": "JSONB", "default": {}}
      },
      "indexes": ["date", "tags"],
      "relations": []
    }
  },
  "metadata_fields": {
    "memories": {
      "experimental": ["dream_recall", "weather"],
      "promoted": []
    }
  }
}
```

### schemas/evolution_log.json
```json
{
  "migrations": [
    {
      "id": "001",
      "timestamp": "2026-02-11T03:00:00+08:00",
      "description": "Initial schema",
      "type": "create",
      "status": "completed"
    },
    {
      "id": "002",
      "timestamp": "2026-02-11T03:16:19+08:00",
      "description": "Add sleep_quality to memories",
      "type": "alter",
      "status": "pending_approval",
      "ai_suggestion": true,
      "user_request": "我想追蹤睡眠品質"
    }
  ]
}
```

---

## AI 使用指南

### 當用戶說：「我想追蹤 X」

```python
# AI 執行流程
1. 讀取 schemas/registry.json
2. 分析 X 的特性（數值？文字？關聯？）
3. 檢查 metadata_fields 中是否已有類似欄位
4. 生成 3 個方案並比較
5. 詢問用戶選擇
6. 生成遷移腳本
7. 更新 Python models
8. 執行測試
9. 記錄到 evolution_log.json
```

### 決策樹（AI 內部邏輯）

```python
def suggest_schema_change(user_request):
    # 1. 解析需求
    metric_type = analyze_request(user_request)
    
    # 2. 檢查現有結構
    current_schema = load_registry()
    
    # 3. 生成建議
    if metric_type == "simple_numeric":
        return [
            Option("JSONB", complexity=1, performance=3),
            Option("New Column", complexity=3, performance=5),
        ]
    elif metric_type == "complex_tracking":
        return [
            Option("JSONB", complexity=2, performance=3),
            Option("Related Table", complexity=5, performance=5),
        ]
    
    # 4. 顯示給用戶
    present_options_to_user()
```

---

## 用戶互動範例

### 範例 1: 簡單指標

```
User: "我想追蹤睡眠品質"

AI: 我分析了您的需求，這是一個簡單的數值指標（1-10）。
    我建議以下方案：

    【方案 A】使用 JSONB metadata（推薦）
    - 優點：立即可用，無需遷移
    - 缺點：查詢效能較低
    - 實現時間：< 1 分鐘
    
    【方案 B】新增專用欄位 sleep_quality
    - 優點：查詢效能高，可建立索引
    - 缺點：需要資料庫遷移
    - 實現時間：5 分鐘
    
    您想選擇哪個方案？

User: "選 A，先試試看"

AI: 好的！我已經更新了代碼：
    
    1. ✅ 更新 SorterAgent 提示詞（識別睡眠品質）
    2. ✅ 更新 API Schema（接受 sleep_quality）
    3. ✅ 更新前端 CaptureView（顯示睡眠品質輸入）
    
    現在您可以在日記中寫「睡眠品質 8/10」，AI 會自動提取。
    
    如果 30 天後您覺得有用，我可以幫您升級為專用欄位。
```

### 範例 2: 複雜追蹤

```
User: "我想追蹤每天的運動記錄，包括類型、時長、強度"

AI: 這是一個複雜的追蹤需求，我建議創建專用的關聯表。
    
    【建議方案】創建 exercise_logs 表
    
    結構預覽：
    ```sql
    CREATE TABLE exercise_logs (
        id UUID PRIMARY KEY,
        memory_id UUID REFERENCES memories(id),
        exercise_type TEXT, -- 'running', 'gym', 'yoga'
        duration_minutes INT,
        intensity INT CHECK (1-10),
        notes TEXT,
        created_at TIMESTAMPTZ
    );
    ```
    
    這樣設計的好處：
    - 一天可以記錄多次運動
    - 可以獨立查詢運動數據
    - 可以生成運動統計報表
    
    是否執行此遷移？

User: "好，執行"

AI: 開始執行遷移...
    
    [1/5] ✅ 生成 SQL 遷移腳本
    [2/5] ✅ 創建 Pydantic Model (ExerciseLog)
    [3/5] ✅ 創建 API 路由 (/api/v1/exercises)
    [4/5] ✅ 更新前端組件
    [5/5] ✅ 執行資料庫遷移
    
    完成！您現在可以使用新的運動追蹤功能了。
    
    我已經記錄此次變更到：
    - migrations/003_add_exercise_logs.sql
    - docs/CHANGELOG.md
```

---

## 實現優先級

### Phase 1: 基礎設施（立即實現）
- [x] 創建 schemas/registry.json
- [x] 創建 schemas/evolution_log.json
- [ ] 實現 migration_generator.py
- [ ] 實現 schema_validator.py

### Phase 2: AI 整合（本週）
- [ ] 訓練 AI 讀取 registry.json
- [ ] 實現決策樹邏輯
- [ ] 創建互動式建議系統

### Phase 3: 自動化（下週）
- [ ] 自動生成 Pydantic models
- [ ] 自動更新 API 路由
- [ ] 自動執行測試

---

## 安全機制

### 1. 遷移前檢查
```python
def validate_migration(sql):
    checks = [
        no_drop_without_backup(),
        has_rollback_plan(),
        preserves_data_integrity(),
        follows_naming_convention()
    ]
    return all(checks)
```

### 2. 用戶確認流程
```
AI: 這是遷移腳本預覽：
    [顯示 SQL]
    
    影響範圍：
    - 修改表：memories
    - 新增欄位：sleep_quality
    - 預計執行時間：< 1 秒
    - 可回滾：是
    
    輸入 "CONFIRM" 以執行，或 "CANCEL" 取消
```

### 3. 自動備份
```python
before_migration():
    create_backup()
    
after_migration():
    verify_data_integrity()
    if not valid:
        rollback()
```

---

## 下一步

1. **立即實現** `schemas/registry.json`（我現在就做）
2. **訓練 AI** 讀取和理解 registry
3. **測試工作流程** 用「睡眠品質」作為第一個案例
4. **迭代優化** 根據實際使用調整

準備好了嗎？我現在就開始實現基礎設施！
