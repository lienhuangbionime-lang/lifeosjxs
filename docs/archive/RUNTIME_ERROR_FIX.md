# Runtime Error 修復說明

## 問題
```
⚠ Fast Refresh had to perform a full reload due to a runtime error.
```

## 原因
Framer Motion 的 `maxHeight` 屬性不支持直接在動畫中使用字符串值（如 `'400px'`）。

## 錯誤代碼
```tsx
<motion.div
  initial={{ opacity: 0, maxHeight: 0 }}
  animate={{ opacity: 1, maxHeight: '400px' }}  // ❌ 錯誤：不支持字符串
  exit={{ opacity: 0, maxHeight: 0 }}
>
```

## 修復方案
使用 `height: 'auto'` 進行動畫，並通過 `style` 屬性設置 `maxHeight`：

```tsx
<motion.div
  initial={{ opacity: 0, height: 0 }}
  animate={{ opacity: 1, height: 'auto' }}  // ✅ 正確：使用 auto
  exit={{ opacity: 0, height: 0 }}
  transition={{ duration: 0.3 }}
  style={{ maxHeight: '400px' }}  // ✅ 通過 style 設置最大高度
  className="mb-8 overflow-hidden relative z-10 flex-shrink-0"
>
```

## 效果
- ✅ 動畫正常運行
- ✅ 內容區域最大高度限制為 400px
- ✅ 超出部分可滾動（內部 div 有 `max-h-[250px] overflow-y-auto`）
- ✅ SAVE 按鈕始終可見

## 相關文件
- `frontend-body/components/CaptureView.tsx` (已修復)
