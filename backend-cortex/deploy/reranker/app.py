# [v6.0] Remote Reranker Microservice
from fastapi import FastAPI, Body
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
import logging

app = FastAPI(title="LifeOS Reranker Service (v7.1 Turbo)")
# [v7.1] Use high-speed MiniLM for cloud CPU environments
model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

@app.post("/rerank")
async def rerank(query: str = Body(...), documents: List[Dict[str, Any]] = Body(...)):
    if not documents:
        return {"results": []}
    
    pairs = [[query, doc.get("content", "")] for doc in documents]
    scores = model.predict(pairs)
    
    # Sort docs by scores
    results = []
    for i, doc in enumerate(documents):
        results.append({"id": doc.get("id"), "score": float(scores[i])})
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": [r["id"] for r in results]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
