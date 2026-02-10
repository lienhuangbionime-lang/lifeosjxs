# CaptureView 分析結果顯示修復

## 問題描述
1. **分析結果不顯示**：AI 分析完成後，結果會立即消失
2. **頁面閃退**：表單在設置分析結果後立即被重置

## 根本原因
在 `handleSubmit` 函數中，代碼流程是：
1. 調用 API 獲取分析結果
2. 設置 `analysis` 狀態
3. **立即重置表單**（`setText('')` 和 `setActiveHabits({})`）

這導致用戶還沒看到分析結果，表單就被清空了。

## 修復方案

### 1. 條件性表單重置
```tsx
// 之前：總是重置表單
setText('');
setActiveHabits({});

// 修復後：只在 SAVE 時重置，ANALYZE 時保留輸入
if (skipAi) {
  setText('');
  setActiveHabits({});
}
```

**邏輯：**
- **SAVE 按鈕**（`skipAi=true`）：直接儲存，不需要查看分析，可以立即清空表單
- **INGEST & ANALYZE 按鈕**（`skipAi=false`）：需要查看分析結果，保留輸入內容

### 2. 添加"清除並新建"按鈕
在分析結果的終端底部添加了一個按鈕，讓用戶在查看完分析後可以手動清除表單：

```tsx
<button
  onClick={() => {
    setAnalysis(null);
    setText('');
    setActiveHabits({});
  }}
  className="..."
>
  Clear & New Entry
</button>
```

### 3. 修復內容引用
```tsx
// 之前：使用 analysis 變量（可能還沒更新）
content: analysis || text

// 修復後：使用 response.data 中的實際值
content: response.data?.markdown_body || text
```

## 用戶流程

### 使用 INGEST & ANALYZE
1. 輸入內容
2. 點擊 "INGEST & ANALYZE"
3. ✅ 分析結果顯示在終端中
4. ✅ 原始輸入保留在文本框中
5. 用戶可以：
   - 複製分析結果（Copy to Clipboard）
   - 關閉分析結果（X 按鈕）
   - 清除並開始新條目（Clear & New Entry）

### 使用 SAVE
1. 輸入內容
2. 點擊 "SAVE"
3. ✅ 直接儲存（跳過 AI）
4. ✅ 表單自動清空
5. ✅ 顯示成功提示

## 效果

✅ **分析結果正常顯示**
- AI 分析完成後，結果會顯示在終端中
- 用戶可以完整查看分析內容

✅ **不會閃退**
- 表單不會在顯示分析前被重置
- 用戶體驗流暢

✅ **靈活的工作流程**
- SAVE：快速儲存，自動清空
- ANALYZE：查看分析，手動清空

## 相關文件
- `frontend-body/components/CaptureView.tsx` (已修復)
