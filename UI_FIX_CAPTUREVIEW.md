# CaptureView 滾動佈局修復

## 問題
即使限制了分析區域的高度，當內容很長時，SAVE 按鈕仍然會被推到畫面外。

## 解決方案
**改用可滾動佈局**，讓用戶可以自由滾動查看所有內容。

## 修改內容

### 1. 主容器 - 啟用垂直滾動
```tsx
// 之前：overflow-hidden (隱藏溢出內容)
<div className="flex flex-col h-full p-6 animate-fade-in relative max-w-3xl mx-auto w-full overflow-hidden">

// 修復後：overflow-y-auto (允許垂直滾動)
<div className="flex flex-col h-full p-6 pb-32 animate-fade-in relative max-w-3xl mx-auto w-full overflow-y-auto custom-scrollbar">
```

### 2. 輸入區域 - 使用最小高度
```tsx
// 之前：固定高度 h-[200px]
<div className="relative group mb-8 flex-shrink-0 h-[200px]">

// 修復後：最小高度 min-h-[200px] (可以自然擴展)
<div className="relative group mb-8 min-h-[200px]">
```

### 3. 分析區域 - 移除高度限制
```tsx
// 之前：限制最大高度 400px
<motion.div
  className="mb-8 overflow-hidden relative z-10 flex-shrink-0"
  style={{ maxHeight: '400px' }}
>

// 修復後：自然高度，無限制
<motion.div
  className="mb-8 overflow-hidden relative z-10"
>
```

### 4. 終端內容 - 移除滾動限制
```tsx
// 之前：max-h-[250px] (內部滾動)
<div className="max-h-[250px] overflow-y-auto custom-scrollbar">

// 修復後：完整顯示 (外部滾動)
<div className="overflow-y-auto custom-scrollbar">
```

### 5. 按鈕區域 - 簡化佈局
```tsx
// 之前：複雜的固定佈局
<div className="flex justify-end items-center gap-4 relative z-10 flex-shrink-0 mt-auto pt-6 pb-6 bg-gradient-to-t from-[#0a0f1e] via-[#0a0f1e] to-transparent">

// 修復後：簡單的間距
<div className="flex justify-end items-center gap-4 relative z-10 mb-8">
```

## 效果

✅ **整個頁面可以自由滾動**
- 用戶可以向下滾動查看所有內容
- SAVE 和 INGEST 按鈕永遠可以訪問
- 不會有內容被隱藏或截斷

✅ **更自然的用戶體驗**
- 符合一般網頁的滾動習慣
- 不需要在多個區域之間切換滾動
- 底部留白 (pb-32) 確保按鈕不會貼邊

✅ **適應任意長度的內容**
- AI 分析結果再長也能完整顯示
- 不會因為內容過長而出現佈局問題

## 使用方式

1. 輸入內容
2. 點擊 "INGEST & ANALYZE" 或 "SAVE"
3. 如果分析結果很長，**向下滾動**即可看到按鈕
4. 點擊按鈕完成操作

## 相關文件
- `frontend-body/components/CaptureView.tsx` (已修復)
