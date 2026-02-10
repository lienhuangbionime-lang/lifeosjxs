# Context Engineering Implementation Guide
**從開發者進化為 AI 系統架構師**

---

## 🎯 目標

建立一個完整的 **Context Engineering** 系統，讓 AI 編碼助手能夠：
1. 理解整個專案架構
2. 遵循編碼規範
3. 產出符合標準的代碼
4. 持續學習和改進

---

## ✅ 已完成的基礎建設

### 1. 核心文檔
- ✅ `SYSTEM_CONTEXT.md` - 完整系統上下文（單一真相來源）
- ✅ `.cursorrules` - Cursor AI 規則文件

### 2. 文檔結構
```
SYSTEM_CONTEXT.md
├── 專案使命與哲學
├── 架構概覽
├── 技術棧詳細說明
├── 編碼標準（TypeScript + Python）
├── 資料庫 Schema
├── UI/UX 指南
├── API 整合規範
├── 禁止事項清單
├── Git 工作流程
├── 測試指南
└── 迭代協議
```

---

## 🚀 使用方式

### 方式一：在 Cursor 中使用

#### 1. 自動載入（推薦）
Cursor 會自動讀取 `.cursorrules` 文件。

#### 2. 手動引用
在對話中明確引用：
```
@SYSTEM_CONTEXT.md 請幫我創建一個新的 Dashboard 卡片組件
```

#### 3. 專案範圍提示
在 Cursor 設定中，將 `SYSTEM_CONTEXT.md` 設為專案範圍的上下文。

### 方式二：在 Antigravity 中使用

#### 1. 在提示中引用
```
請參考 SYSTEM_CONTEXT.md 中的規範，幫我實現 XXX 功能
```

#### 2. 提供關鍵片段
如果 AI 沒有自動讀取，可以複製相關片段到對話中。

---

## 📋 實戰工作流程

### Scenario 1: 創建新組件

#### Step 1: 提供上下文
```
我需要創建一個新的數據可視化組件。
請參考 SYSTEM_CONTEXT.md 中的：
- Component Structure
- Styling Rules
- UI/UX Guidelines
```

#### Step 2: 明確需求
```
組件需求：
- 顯示月度趨勢圖表
- 使用 Recharts
- 支持響應式設計
- 使用 Tailwind CSS
```

#### Step 3: 驗證輸出
檢查生成的代碼是否符合：
- ✅ 使用 Tailwind CSS（沒有 inline styles）
- ✅ 使用 TypeScript 類型
- ✅ 使用 Framer Motion 動畫
- ✅ 遵循命名規範

#### Step 4: 迭代改進
如果有錯誤：
```
這段代碼使用了 inline styles，違反了 SYSTEM_CONTEXT.md 的規範。
請改用 Tailwind CSS classes。
```

### Scenario 2: 創建 API 端點

#### Step 1: 提供上下文
```
我需要創建一個新的 API 端點來處理記憶數據。
請參考 SYSTEM_CONTEXT.md 中的：
- API Endpoint Structure
- Pydantic Models
- Error Handling
```

#### Step 2: 明確需求
```
端點需求：
- POST /api/v1/memories
- 接收 content, mood, focus, energy
- 使用 Pydantic 驗證
- 儲存到 Supabase
- 返回標準格式
```

#### Step 3: 驗證輸出
檢查生成的代碼是否符合：
- ✅ 使用 async/await
- ✅ 使用 Pydantic v2
- ✅ 使用 HTTPException
- ✅ 返回標準格式

### Scenario 3: 修復 Bug

#### Step 1: 描述問題
```
在 CardStackDashboard 組件中，卡片滑動在手機上不流暢。
請參考 SYSTEM_CONTEXT.md 中的 UI/UX Guidelines 和 Mobile Optimization。
```

#### Step 2: 提供上下文
```
相關文件：
- frontend-body/components/CardStackDashboard.tsx
- MOBILE_DRAG_FIX.md
```

#### Step 3: 驗證修復
測試修復後的代碼：
- ✅ 手機上滑動流暢
- ✅ 沒有破壞現有功能
- ✅ 遵循編碼規範

---

## 🔄 迭代改進流程

### 當 AI 產生錯誤代碼時

#### 1. 識別問題
```
問題：AI 使用了 styled-components
原因：SYSTEM_CONTEXT.md 中沒有明確禁止
```

#### 2. 更新文檔
在 `SYSTEM_CONTEXT.md` 的 "Forbidden Practices" 中添加：
```markdown
#### Frontend
- ❌ Use CSS-in-JS libraries (styled-components, emotion, etc.)
```

#### 3. 重新生成
```
請重新生成代碼，遵循更新後的 SYSTEM_CONTEXT.md 規範。
特別注意：不要使用 CSS-in-JS，只使用 Tailwind CSS。
```

#### 4. 驗證改進
確認 AI 下次不會再犯同樣的錯誤。

---

## 📊 效果評估

### 評估指標

#### 1. 代碼品質
- **一致性**：新代碼是否符合現有風格？
- **正確性**：是否遵循技術棧規範？
- **可維護性**：是否易於理解和修改？

#### 2. 開發效率
- **首次正確率**：AI 第一次生成的代碼有多少是可用的？
- **迭代次數**：需要多少次修正才能達到要求？
- **時間節省**：相比手動編碼節省了多少時間？

#### 3. 學習效果
- **錯誤減少**：同類錯誤是否減少？
- **上下文理解**：AI 是否能理解複雜需求？
- **主動遵循**：AI 是否主動遵循規範？

### 追蹤方式

#### 創建 Context Engineering Log
```markdown
# Context Engineering Log

## 2026-02-10
### Issue: AI 使用了 inline styles
- **Context**: 創建新組件時
- **Root Cause**: 規範不夠明確
- **Fix**: 更新 SYSTEM_CONTEXT.md，添加明確禁止
- **Result**: 後續生成正確

## 2026-02-11
### Issue: API 端點沒有錯誤處理
- **Context**: 創建新 API 端點
- **Root Cause**: 沒有提供錯誤處理範例
- **Fix**: 添加錯誤處理模式到 SYSTEM_CONTEXT.md
- **Result**: 改進明顯
```

---

## 🎓 進階技巧

### 1. 分層上下文

#### 全局上下文（SYSTEM_CONTEXT.md）
- 適用於整個專案的規範
- 技術棧、架構、編碼標準

#### 模組上下文（README.md in subdirectories）
- 適用於特定模組的規範
- 例如：`frontend-body/components/README.md`

#### 任務上下文（對話中提供）
- 適用於當前任務的具體需求
- 例如：「這個組件需要支持拖曳」

### 2. 上下文模板

#### 新功能開發模板
```
我需要開發 [功能名稱]。

請參考：
- SYSTEM_CONTEXT.md 的 [相關章節]
- [相關文件路徑]

需求：
1. [需求1]
2. [需求2]
3. [需求3]

約束：
- [約束1]
- [約束2]

預期輸出：
- [輸出1]
- [輸出2]
```

#### Bug 修復模板
```
Bug 描述：[問題描述]

重現步驟：
1. [步驟1]
2. [步驟2]

預期行為：[預期]
實際行為：[實際]

相關文件：
- [文件1]
- [文件2]

請參考 SYSTEM_CONTEXT.md 中的 [相關章節] 來修復。
```

### 3. 上下文優化

#### 定期審查
每週審查 `SYSTEM_CONTEXT.md`：
- 是否有新的模式需要記錄？
- 是否有過時的規範需要更新？
- 是否有重複的內容需要整合？

#### 版本控制
使用 Git 追蹤 `SYSTEM_CONTEXT.md` 的變更：
```bash
git log SYSTEM_CONTEXT.md
```

#### 團隊同步
如果有團隊成員，確保大家都了解最新的上下文：
- 定期分享更新
- 討論新增的規範
- 收集反饋和建議

---

## 🎯 成功指標

### 短期目標（1-2 週）
- ✅ AI 生成的代碼 80% 符合規範
- ✅ 減少 50% 的代碼修正時間
- ✅ 建立完整的上下文文檔

### 中期目標（1-2 月）
- ✅ AI 生成的代碼 95% 符合規範
- ✅ 開發效率提升 2-3 倍
- ✅ 形成穩定的工作流程

### 長期目標（3-6 月）
- ✅ AI 能夠理解複雜的架構決策
- ✅ 幾乎不需要手動修正代碼
- ✅ 成為 AI 系統架構師

---

## 💡 最佳實踐

### 1. 保持上下文更新
每次發現新模式或規範時，立即更新 `SYSTEM_CONTEXT.md`。

### 2. 明確優先級
在 `SYSTEM_CONTEXT.md` 中使用 **ALWAYS**、**NEVER** 等強調詞。

### 3. 提供範例
好的範例勝過長篇解釋。

### 4. 迭代改進
不要期望一次就完美，持續改進。

### 5. 記錄決策
記錄為什麼選擇某個規範，幫助未來理解。

---

## 🚀 下一步行動

### 立即行動（今天）
1. ✅ 閱讀 `SYSTEM_CONTEXT.md`
2. ✅ 在 Cursor 中測試 `.cursorrules`
3. ✅ 嘗試用新的工作流程創建一個組件

### 本週行動
1. 使用新工作流程開發所有新功能
2. 記錄 AI 的錯誤和改進
3. 更新 `SYSTEM_CONTEXT.md`

### 本月行動
1. 建立 Context Engineering Log
2. 評估效果並調整策略
3. 分享經驗和最佳實踐

---

## 📚 參考資源

### 內部文檔
- `SYSTEM_CONTEXT.md` - 完整系統上下文
- `.cursorrules` - Cursor AI 規則
- `MOBILE_DRAG_FIX.md` - 手機優化案例
- `CARD_STACK_DASHBOARD.md` - 組件開發案例

### 外部資源
- [Cursor Documentation](https://cursor.sh/docs)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [AI-Assisted Development Best Practices](https://github.com/features/copilot)

---

## 🎉 總結

Context Engineering 不是一門新技術，而是一種**思維方式**：

1. **結構化思維**：將知識系統化組織
2. **持續改進**：每次錯誤都是學習機會
3. **知識複用**：一次記錄，永久受益

通過建立完整的系統上下文，我們不僅提升了 AI 的能力，更重要的是**提升了整個開發流程的品質和效率**。

這就是從「開發者」進化為「AI 系統架構師」的關鍵一步。

---

**開始你的 Context Engineering 之旅吧！** 🚀

---

**Created**: 2026-02-10  
**Author**: Commander 蒼禾 + Cortex AI  
**Version**: 1.0
