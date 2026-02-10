# LifeOS v3.1 - Question-Driven Architecture
**從「記錄系統」到「問答系統」的範式轉移**

---

## 🎯 核心目標

### 不是記錄，而是回答
```
傳統日記系統：記錄 → 儲存 → 查詢
LifeOS v3.1：  記錄 → 理解 → 回答 → 釐清
```

### 三大核心場景

#### 1. 看關聯性問系統
**用戶問**：
- 「這個專案和我之前做的哪些專案有關？」
- 「我在類似情況下做過什麼決策？」
- 「這個問題我之前遇過嗎？」

**系統回答**：
- 自動找出相關專案
- 提取過去的決策模式
- 顯示解決方案和結果

#### 2. 看專案問系統
**用戶問**：
- 「這個專案目前的狀態如何？」
- 「還有哪些待辦事項？」
- 「類似專案我花了多少時間？」
- 「股票 XYZ 的研究進度？」（股票也是專案）

**系統回答**：
- 即時專案狀態
- 自動整理待辦
- 時間估算和預測
- 投資研究摘要

#### 3. 看日記問系統
**用戶問**：
- 「那天我為什麼做這個決定？」
- 「我的心情趨勢和專案進度有關聯嗎？」
- 「我在壓力大的時候通常做什麼？」

**系統回答**：
- 決策脈絡還原
- 自動關聯分析
- 行為模式識別

---

## 🏗️ 新架構設計

### 系統分層

```
┌─────────────────────────────────────────────┐
│         Question Interface (問答介面)         │
│  「這個專案和之前的有什麼關聯？」              │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│      Question Understanding (問題理解)        │
│  - 意圖識別：查詢關聯 / 查詢狀態 / 查詢決策    │
│  - 實體抽取：專案名稱、時間範圍、關鍵詞        │
│  - 上下文補全：根據當前視圖補充缺失信息        │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│      Knowledge Graph (知識圖譜)              │
│  - 專案節點：所有專案（含股票）                │
│  - 日記節點：所有日記條目                      │
│  - 關聯邊：相似度、時間、標籤、決策            │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│      Answer Generation (答案生成)            │
│  - 檢索相關節點                               │
│  - 排序和過濾                                 │
│  - 生成自然語言回答                           │
│  - 提供可視化（圖表、時間軸、關聯圖）          │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│   Clarification Engine (釐清引擎)            │
│  - 識別模糊問題                               │
│  - 主動提問澄清                               │
│  - 建議相關問題                               │
│  - 引導深入探索                               │
└─────────────────────────────────────────────┘
```

---

## 🔍 核心組件設計

### 1. Question Understanding (問題理解)

#### 意圖分類
```typescript
enum QuestionIntent {
  QUERY_RELATION = 'relation',      // 查詢關聯
  QUERY_STATUS = 'status',          // 查詢狀態
  QUERY_DECISION = 'decision',      // 查詢決策
  QUERY_PATTERN = 'pattern',        // 查詢模式
  QUERY_TIMELINE = 'timeline',      // 查詢時間線
  QUERY_COMPARISON = 'comparison',  // 查詢比較
}

interface ParsedQuestion {
  intent: QuestionIntent;
  entities: {
    projects?: string[];      // 專案名稱
    dates?: DateRange;        // 時間範圍
    keywords?: string[];      // 關鍵詞
    metrics?: string[];       // 指標（心情、專注等）
  };
  context: {
    current_view: 'project' | 'diary' | 'graph';
    current_item?: string;    // 當前查看的專案/日記
  };
}
```

#### 實體抽取範例
```
用戶問：「這個專案和我之前做的有什麼關聯？」

解析結果：
{
  intent: 'relation',
  entities: {
    projects: ['當前專案'],  // 從上下文推斷
    keywords: []
  },
  context: {
    current_view: 'project',
    current_item: 'LifeOS v3.1'
  }
}
```

### 2. Knowledge Graph (知識圖譜)

#### 節點類型
```typescript
interface ProjectNode {
  id: string;
  type: 'project';
  name: string;
  category: 'software' | 'stock' | 'research' | 'personal';
  status: 'active' | 'completed' | 'archived';
  created_at: Date;
  metadata: {
    tags: string[];
    description: string;
    goals: string[];
  };
  embedding: number[];  // 768-dim vector for similarity
}

interface DiaryNode {
  id: string;
  type: 'diary';
  date: Date;
  content: string;
  metrics: {
    mood: number;
    focus: number;
    energy: number;
  };
  mentioned_projects: string[];  // 提到的專案
  decisions: Decision[];         // 做的決策
  embedding: number[];
}

interface Decision {
  description: string;
  context: string;
  outcome?: string;
  related_projects: string[];
}
```

#### 關聯邊類型
```typescript
interface RelationEdge {
  from: string;  // Node ID
  to: string;    // Node ID
  type: 'similar' | 'temporal' | 'causal' | 'reference';
  weight: number;  // 0-1, 關聯強度
  metadata: {
    reason?: string;      // 為什麼有關聯
    created_at: Date;
  };
}

// 範例
{
  from: 'lifeos-v3',
  to: 'lifeos-v2',
  type: 'similar',
  weight: 0.85,
  metadata: {
    reason: '都是個人知識管理系統，使用相似技術棧',
    created_at: '2026-02-10'
  }
}
```

### 3. Answer Generation (答案生成)

#### 回答模板
```typescript
interface Answer {
  question: string;
  answer: string;           // 自然語言回答
  confidence: number;       // 0-1, 信心度
  sources: Source[];        // 來源
  visualizations: Viz[];    // 可視化
  related_questions: string[];  // 相關問題建議
}

interface Source {
  type: 'project' | 'diary' | 'decision';
  id: string;
  title: string;
  excerpt: string;
  relevance: number;  // 0-1
}

interface Viz {
  type: 'graph' | 'timeline' | 'chart';
  data: any;
  description: string;
}
```

#### 回答範例
```typescript
// 問題：「這個專案和我之前做的有什麼關聯？」
{
  question: "這個專案和我之前做的有什麼關聯？",
  answer: "LifeOS v3.1 與你之前的 3 個專案高度相關：\n\n1. **LifeOS v2.0** (相似度 85%)\n   - 都是個人知識管理系統\n   - 使用 Python + React 技術棧\n   - 你在 2025 年 8 月完成\n\n2. **Second Brain Project** (相似度 72%)\n   - 都關注知識組織和檢索\n   - 你在日記中提到這是 v3.1 的靈感來源\n\n3. **AI Assistant Prototype** (相似度 68%)\n   - 都使用 Gemini API\n   - 你在 2026 年 1 月做過相關研究",
  confidence: 0.92,
  sources: [
    {
      type: 'project',
      id: 'lifeos-v2',
      title: 'LifeOS v2.0',
      excerpt: '個人知識管理系統，使用 FastAPI + Next.js...',
      relevance: 0.85
    },
    {
      type: 'diary',
      id: '2026-01-15',
      title: '2026-01-15 日記',
      excerpt: '今天研究了 Gemini API，想用在新的 LifeOS 版本...',
      relevance: 0.78
    }
  ],
  visualizations: [
    {
      type: 'graph',
      data: { nodes: [...], edges: [...] },
      description: '專案關聯圖'
    }
  ],
  related_questions: [
    '這些專案中哪個最成功？',
    'LifeOS v2.0 遇到了什麼問題？',
    '我在這些專案上花了多少時間？'
  ]
}
```

### 4. Clarification Engine (釐清引擎)

#### 模糊問題識別
```typescript
interface ClarificationNeeded {
  original_question: string;
  ambiguities: Ambiguity[];
  suggested_questions: string[];
}

interface Ambiguity {
  type: 'missing_entity' | 'time_range' | 'multiple_matches';
  description: string;
  options?: string[];
}

// 範例
用戶問：「這個專案進度如何？」

系統識別：
{
  original_question: "這個專案進度如何？",
  ambiguities: [
    {
      type: 'missing_entity',
      description: '你有 5 個進行中的專案，請問你指的是哪一個？',
      options: [
        'LifeOS v3.1',
        'TSMC 股票研究',
        'Context Engineering 文檔',
        '個人網站重構',
        'AI Trading Bot'
      ]
    }
  ],
  suggested_questions: [
    'LifeOS v3.1 的進度如何？',
    'TSMC 股票研究的進度如何？',
    '所有進行中專案的進度總覽？'
  ]
}
```

#### 主動引導
```typescript
interface GuidedExploration {
  current_answer: Answer;
  next_steps: NextStep[];
}

interface NextStep {
  question: string;
  reason: string;
  priority: number;  // 1-10
}

// 範例
系統回答完「這個專案和之前的有什麼關聯？」後：

{
  current_answer: { ... },
  next_steps: [
    {
      question: '這些相關專案中，哪個最成功？為什麼？',
      reason: '了解成功模式可以幫助當前專案',
      priority: 9
    },
    {
      question: 'LifeOS v2.0 遇到了什麼問題？如何避免？',
      reason: '從過去的錯誤中學習',
      priority: 8
    },
    {
      question: '我在這些專案上的時間分配是怎樣的？',
      reason: '幫助估算當前專案所需時間',
      priority: 7
    }
  ]
}
```

---

## 🎨 UI 設計：問答優先

### 主介面：對話式

```
┌─────────────────────────────────────────────┐
│  LifeOS - Your Second Brain                 │
├─────────────────────────────────────────────┤
│                                              │
│  💬 問我任何關於你的專案、日記、決策的問題    │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ 這個專案和我之前做的有什麼關聯？      │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  🤖 LifeOS v3.1 與你之前的 3 個專案高度相關： │
│                                              │
│  📊 [專案關聯圖]                             │
│                                              │
│  1. LifeOS v2.0 (相似度 85%)                │
│     - 都是個人知識管理系統                   │
│     - 使用 Python + React                   │
│     [查看詳情]                               │
│                                              │
│  2. Second Brain Project (相似度 72%)       │
│     - 都關注知識組織                         │
│     [查看詳情]                               │
│                                              │
│  💡 你可能還想問：                           │
│  • 這些專案中哪個最成功？                    │
│  • LifeOS v2.0 遇到了什麼問題？             │
│  • 我在這些專案上花了多少時間？              │
│                                              │
└─────────────────────────────────────────────┘
```

### 快捷問題面板

```
┌─────────────────────────────────────────────┐
│  🔥 常用問題                                 │
├─────────────────────────────────────────────┤
│  📂 專案相關                                 │
│  • 我有哪些進行中的專案？                    │
│  • 本週專案進度如何？                        │
│  • TSMC 股票研究的最新進展？                │
│                                              │
│  📝 日記相關                                 │
│  • 最近一週我的心情趨勢？                    │
│  • 我在壓力大時通常做什麼？                  │
│  • 上次做類似決策是什麼時候？                │
│                                              │
│  🔗 關聯相關                                 │
│  • 這個問題我之前遇過嗎？                    │
│  • 類似專案的成功率如何？                    │
│  • 我的決策模式有什麼特點？                  │
└─────────────────────────────────────────────┘
```

---

## 🚀 實現計劃

### Phase 1: 問題理解 (2 週)
- [ ] 實現意圖分類模型
- [ ] 實現實體抽取
- [ ] 實現上下文補全
- [ ] 建立問題模板庫

### Phase 2: 知識圖譜 (3 週)
- [ ] 設計圖譜 Schema
- [ ] 實現自動建圖（從專案和日記）
- [ ] 實現相似度計算（embedding）
- [ ] 實現關聯推理

### Phase 3: 答案生成 (2 週)
- [ ] 實現檢索系統
- [ ] 實現答案模板
- [ ] 實現可視化生成
- [ ] 實現相關問題推薦

### Phase 4: 釐清引擎 (2 週)
- [ ] 實現模糊問題識別
- [ ] 實現主動提問
- [ ] 實現引導探索
- [ ] 實現學習用戶偏好

### Phase 5: UI 整合 (1 週)
- [ ] 對話式介面
- [ ] 快捷問題面板
- [ ] 可視化展示
- [ ] 移動端優化

---

## 💡 關鍵技術

### 1. 語義搜索
```python
# 使用 Gemini Embedding API
from google.generativeai import embed_content

# 為專案和日記生成 embedding
project_embedding = embed_content(
    model="models/text-embedding-004",
    content=project_description
)

# 計算相似度
similarity = cosine_similarity(query_embedding, project_embedding)
```

### 2. 知識圖譜
```python
# 使用 NetworkX 或 Neo4j
import networkx as nx

G = nx.DiGraph()
G.add_node('lifeos-v3', type='project', ...)
G.add_node('lifeos-v2', type='project', ...)
G.add_edge('lifeos-v3', 'lifeos-v2', 
           type='similar', weight=0.85)

# 查詢相關專案
related = nx.neighbors(G, 'lifeos-v3')
```

### 3. 自然語言生成
```python
# 使用 Gemini API 生成回答
prompt = f"""
基於以下信息回答問題：

問題：{question}

相關專案：
{related_projects}

相關日記：
{related_diaries}

請用自然、友善的語氣回答，並提供具體例子。
"""

answer = model.generate_content(prompt)
```

---

## 🎯 成功指標

### 用戶體驗
- ✅ 90% 的問題能被正確理解
- ✅ 80% 的回答被用戶認為有幫助
- ✅ 平均 3 秒內得到回答
- ✅ 用戶主動提問頻率增加

### 系統能力
- ✅ 自動識別 95% 的專案關聯
- ✅ 準確提取 90% 的決策記錄
- ✅ 主動釐清 80% 的模糊問題
- ✅ 推薦的相關問題 70% 被採用

---

## 📚 與現有架構的關係

### 保留
- ✅ Media Core Architecture（資料儲存）
- ✅ Nomad List Style（視覺設計）
- ✅ Context Engineering（開發流程）

### 新增
- ✅ Question Understanding（問題理解層）
- ✅ Knowledge Graph（知識圖譜層）
- ✅ Answer Generation（答案生成層）
- ✅ Clarification Engine（釐清引擎）

### 整合
```
問答系統（新）
    ↓
知識圖譜（新）
    ↓
資料儲存（Media Core）
    ↓
視覺呈現（Nomad List Style）
```

---

**這才是 LifeOS v3.1 的真正核心：一個能自動釐清問題、讓你專注發展新專案的智能問答系統！** 🎯✨

---

**Created**: 2026-02-10  
**Version**: 3.1.0 - Question-Driven  
**Status**: Ready for Implementation
