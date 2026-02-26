---
name: research
description: 用於搜尋外部網路資訊、查證事實與技術調研。
metadata:
  version: "1.0"
  author: "Cortex"
---

# Research Specialist Protocol

## Objective
When internal memories are insufficient or when the user asks about current events/tech trends, activate the web search capability to provide evidence-based insights.

## Activation Triggers
- 使用者詢問「最近」、「最新進展」、「新聞」、「查一下」。
- 現有記憶庫 (RAG) 搜尋結果為空或不相關。
- 使用者明確要求「上網搜尋」。

## Workflow
1. **Analyze Intent**: 確定關鍵搜尋詞 (Keywords)。
2. **Execute Search**: 調用 `search_web` 工具。
3. **Synthesize**: 
   - 結合搜尋結果與 LifeOS 現有的 `SYSTEM_CONTEXT.md` 脈絡。
   - 區分「內部記憶 (Internal)」與「外部檢索 (Web)」。
4. **Insight**: 提供基於搜尋結果的策略性建議。

## Rules
- **Evidence First**: 必須引用搜尋結果中的標題與部分網址作為來源。
- **Concatenation**: 不要只給連結，要給摘要。
- **Relevance**: 確保搜尋內容與使用者的 LifeOS 目標相關。
