# Context Engineering - 快速開始

## 🎯 3 分鐘快速上手

### 已完成 ✅
我們已經為 LifeOS v3.1 建立了完整的 Context Engineering 系統：

1. **SYSTEM_CONTEXT.md** - 完整系統上下文（單一真相來源）
2. **.cursorrules** - Cursor AI 規則文件
3. **CONTEXT_ENGINEERING_GUIDE.md** - 詳細實施指南

---

## 🚀 立即使用

### 在 Cursor 中

#### 方法 1：自動載入（推薦）
Cursor 會自動讀取 `.cursorrules`，無需額外設定。

#### 方法 2：明確引用
```
@SYSTEM_CONTEXT.md 請幫我創建一個新的組件
```

#### 方法 3：複製關鍵規範
如果需要，複製 `SYSTEM_CONTEXT.md` 中的相關片段到對話中。

### 在 Antigravity 中

#### 在提示中引用
```
請參考專案根目錄的 SYSTEM_CONTEXT.md，
特別是 [相關章節]，幫我實現 XXX 功能。
```

---

## 💡 實戰範例

### 範例 1：創建新組件
```
我需要創建一個月度統計卡片組件。

請參考 SYSTEM_CONTEXT.md 中的：
- Component Structure
- Styling Rules (只用 Tailwind CSS)
- UI/UX Guidelines

需求：
- 顯示總條目數、平均心情、深度工作時數
- 使用卡片佈局
- 支持響應式設計
```

### 範例 2：創建 API 端點
```
我需要創建一個 API 端點來獲取月度統計。

請參考 SYSTEM_CONTEXT.md 中的：
- API Endpoint Structure
- Pydantic Models
- Error Handling

端點：GET /api/v1/stats/{month}
返回：總條目數、平均心情、深度工作時數
```

### 範例 3：修復 Bug
```
CardStackDashboard 在手機上滑動不流暢。

請參考 SYSTEM_CONTEXT.md 中的：
- Mobile Optimization
- Framer Motion 使用規範

文件：frontend-body/components/CardStackDashboard.tsx
```

---

## 🔄 工作流程

### 1. 開發新功能
```
提供上下文 → 明確需求 → 生成代碼 → 驗證輸出 → 迭代改進
```

### 2. 修復 Bug
```
描述問題 → 提供上下文 → 生成修復 → 測試驗證 → 更新文檔
```

### 3. 重構代碼
```
說明目標 → 引用規範 → 生成重構 → 驗證品質 → 提交代碼
```

---

## ✅ 驗證清單

### TypeScript/React 代碼
- [ ] 使用 Tailwind CSS（沒有 inline styles）
- [ ] 使用 TypeScript 類型
- [ ] 使用 functional components
- [ ] 使用 'use client' 指令（如果需要）
- [ ] 遵循命名規範（PascalCase）

### Python/FastAPI 代碼
- [ ] 使用 async/await
- [ ] 使用 Pydantic v2
- [ ] 使用 HTTPException
- [ ] 返回標準格式
- [ ] 有錯誤處理

---

## 🎯 關鍵原則

### ALWAYS（總是）
- ✅ 使用 Tailwind CSS
- ✅ 使用 Pydantic v2
- ✅ 使用 async/await
- ✅ 驗證用戶輸入
- ✅ 添加錯誤處理

### NEVER（絕不）
- ❌ 使用 inline styles
- ❌ 使用 CSS-in-JS
- ❌ 使用外部 UI 庫
- ❌ 忽略 TypeScript 錯誤
- ❌ 硬編碼 API URL

---

## 📚 核心文檔

### 必讀
1. **SYSTEM_CONTEXT.md** - 完整系統上下文
2. **.cursorrules** - Cursor AI 規則

### 參考
3. **CONTEXT_ENGINEERING_GUIDE.md** - 詳細實施指南
4. **database-hippocampus/schema.sql** - 資料庫結構

---

## 🔄 迭代改進

### 當 AI 犯錯時
1. **識別問題**：AI 使用了什麼錯誤的方法？
2. **更新文檔**：在 SYSTEM_CONTEXT.md 中添加明確禁止
3. **重新生成**：用更新後的上下文重新生成
4. **驗證改進**：確認 AI 學會了

---

## 💡 專業提示

### 提示 1：明確引用
不要只說「按照規範」，要明確引用：
```
請參考 SYSTEM_CONTEXT.md 的 "Styling Rules" 章節
```

### 提示 2：提供範例
如果有類似的現有代碼，提供參考：
```
參考 CardStackDashboard.tsx 的結構
```

### 提示 3：分步驟
複雜任務分成小步驟：
```
第一步：創建 Pydantic 模型
第二步：創建 API 端點
第三步：添加錯誤處理
```

---

## 🎉 開始使用

### 今天就試試
1. 打開 Cursor
2. 創建一個新組件或 API 端點
3. 在提示中引用 `@SYSTEM_CONTEXT.md`
4. 觀察 AI 生成的代碼品質

### 記錄經驗
創建一個 `CONTEXT_ENGINEERING_LOG.md`：
```markdown
## 2026-02-10
- 使用上下文創建了 XXX 組件
- AI 第一次就生成了正確的代碼
- 節省了 30 分鐘開發時間
```

---

## 📞 需要幫助？

### 查看文檔
- `SYSTEM_CONTEXT.md` - 完整規範
- `CONTEXT_ENGINEERING_GUIDE.md` - 詳細指南

### 常見問題
**Q: AI 沒有遵循規範怎麼辦？**
A: 明確引用相關章節，並在提示中強調。

**Q: 如何更新規範？**
A: 直接編輯 `SYSTEM_CONTEXT.md`，Git 會追蹤變更。

**Q: 可以自定義規則嗎？**
A: 當然！這就是 Context Engineering 的核心。

---

## 🚀 下一步

1. ✅ 閱讀 `SYSTEM_CONTEXT.md`（5 分鐘）
2. ✅ 嘗試創建一個組件（10 分鐘）
3. ✅ 記錄經驗和改進（5 分鐘）

**總共只需 20 分鐘，你就能掌握 Context Engineering！**

---

**開始你的 AI 系統架構師之旅！** 🎯

---

**Created**: 2026-02-10  
**Version**: 1.0
