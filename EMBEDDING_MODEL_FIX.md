# Embedding Model 修復說明

## 問題
```
ERROR: 404 NOT_FOUND
models/text-embedding-004 is not found for API version v1beta
```

## 根本原因
使用了不存在的 embedding 模型名稱 `models/text-embedding-004`。

正確的 Gemini embedding 模型是：`models/embedding-001`

## 修復內容

### 1. RAG Service
**文件：** `backend-cortex/app/services/rag_service.py`

```python
# 之前：錯誤的模型名稱
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# 修復後：正確的模型名稱
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
```

### 2. Memory Service  
**文件：** `backend-cortex/app/services/memory_service.py`

```python
# 之前：錯誤的模型名稱
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# 修復後：正確的模型名稱
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
```

## 重啟後端

修改後需要重啟後端服務器以加載新配置：

```powershell
# 停止當前服務器 (Ctrl+C)
# 然後重啟
cd backend-cortex
python -m uvicorn main:app --reload --port 8000
```

或使用重啟腳本：
```powershell
cd backend-cortex
.\restart_backend.bat
```

## 驗證

重啟後，CortexChat 應該可以正常工作，不會再出現 embedding 錯誤。

## 相關文件
- `backend-cortex/app/services/rag_service.py` (已修復)
- `backend-cortex/app/services/memory_service.py` (已修復)
