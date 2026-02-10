# CortexChat 連接修復

## 問題
```
Connection lost with Cortex.
```

## 根本原因
**端口不匹配**：
- **後端服務器**運行在：`http://localhost:8000`
- **CortexChat 組件**連接到：`http://localhost:8001` ❌

## 修復內容

### 1. 聊天訊息端點
```tsx
// 之前：錯誤的端口
const response = await fetch('http://localhost:8001/api/v1/chat/message', {

// 修復後：正確的端口
const response = await fetch('http://localhost:8000/api/v1/chat/message', {
```

### 2. 文件上傳端點
```tsx
// 之前：錯誤的端口
const res = await fetch('http://localhost:8001/api/v1/chat/ingest', {

// 修復後：正確的端口
const res = await fetch('http://localhost:8000/api/v1/chat/ingest', {
```

## 驗證

### 後端服務器狀態
```bash
# 檢查後端是否運行在 8000 端口
Invoke-WebRequest -Uri http://localhost:8000/api/v1/system/status
```

### 預期結果
```json
{
  "status": "ok",
  "current_model": "gemini-2.5-flash",
  "model_versions": ["gemini-2.5-flash", "gemini-2.5-flash"],
  "remaining_requests": "Free Tier (1500 RPD)"
}
```

## 相關端口配置

### 當前配置
- **後端 (FastAPI/Uvicorn)**: `http://localhost:8000`
- **前端 (Next.js)**: `http://localhost:3000`

### API 客戶端配置
```typescript
// frontend-body/lib/api/client.ts
export const API_BASE = "http://localhost:8000"; // ✅ 正確
```

### CortexChat 配置
```typescript
// frontend-body/components/CortexChat.tsx
fetch('http://localhost:8000/api/v1/chat/message') // ✅ 已修復
fetch('http://localhost:8000/api/v1/chat/ingest')  // ✅ 已修復
```

## 建議改進

為了避免未來的端口不匹配問題，建議使用統一的 API 配置：

```tsx
// 推薦做法：使用 API_BASE 常量
import { API_BASE } from '@/lib/api/client';

const response = await fetch(`${API_BASE}/api/v1/chat/message`, {
  // ...
});
```

## 相關文件
- `frontend-body/components/CortexChat.tsx` (已修復)
- `frontend-body/lib/api/client.ts` (API 配置)
