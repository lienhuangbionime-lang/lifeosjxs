
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
import numpy as np
import os
import httpx
import json
import asyncio

# [v5.4] Safe import ??sentence_transformers is optional.
# If not installed, reranker falls back to recency-only ordering (no crash).
try:
    from sentence_transformers import CrossEncoder
    _CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CrossEncoder = None  # type: ignore
    _CROSS_ENCODER_AVAILABLE = False
    logging.getLogger("cortex.reranker").warning(
        "sentence_transformers not installed. Reranker will use recency-only ordering. "
        "To enable ML reranking: pip install sentence-transformers"
    )

logger = logging.getLogger("cortex.reranker")

class RerankerService:
    _instance = None
    _model = None
    _remote_url = os.getenv("RERANKER_SERVICE_URL") # [v6.0] Cloud Reranker URL

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RerankerService, cls).__new__(cls)
        return cls._instance

    def initialize(self, model_id: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        if not _CROSS_ENCODER_AVAILABLE:
            logger.warning("sentence_transformers not available ??skipping CrossEncoder init.")
            return
        if self._model is None:
            logger.info(f"Loading HuggingFace Reranker model: {model_id}...")
            try:
                self._model = CrossEncoder(model_id)
                logger.info("[OK] Reranker model loaded successfully.")
            except Exception as e:
                logger.error(f"[ERROR] Failed to load reranker model: {e}")
                self._model = None
        else:
            logger.debug("Reranker model already initialized.")

    def rerank(self, query: str, documents: List[Dict[str, Any]], alpha: float = 0.7, beta: float = 0.3) -> List[Dict[str, Any]]:
        """
        Rerank documents using a hybrid score of Semantic Relevance and Recency.
        Final Score = alpha * (Normalized Reranker Score) + beta * (Recency Score)
        """
        if not documents:
            return []
        
        if self._model is None:
            self.initialize()
            if self._model is None:
                # [v6.0] Local model unavailable, attempt remote rerank if configured
                if self._remote_url:
                    logger.info("Local reranker missing ??delegating to Remote Reranker...")
                    # Note: Since rerank is sync and rerank_remote is async, 
                    # we use an event loop wrapper or just keep it simple.
                    # Best is to make RerankerService methods mostly async in v6.0.
                    return asyncio.run(self.rerank_remote(query, documents))
                
                logger.warning("Reranker not initialized, returning original order.")
                return documents

        try:
            # [v7.1] Top-20 Reranking Policy: Limit pairs to avoid CPU bottleneck
            docs_to_rerank = documents[:20]
            remaining_docs = documents[20:]
            
            # 1. Get Semantic Scores from Cross-Encoder
            pairs = [[query, doc.get("content", "")] for doc in docs_to_rerank]
            semantic_scores = self._model.predict(pairs)
            
            def sigmoid(x):
                return 1 / (1 + np.exp(-x))
            
            norm_semantic = sigmoid(semantic_scores)

            # 2. Calculate Recency Scores
            now = datetime.now()
            
            reranked_results = []
            for i, doc in enumerate(docs_to_rerank):
                # Recency Calculation
                created_at_str = doc.get("created_at") or doc.get("date")
                r_score = 0.5
                if created_at_str:
                    try:
                        if isinstance(created_at_str, str):
                            if "T" in created_at_str:
                                dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                            else:
                                dt = datetime.strptime(created_at_str, "%Y-%m-%d")
                            days_old = (now - dt.replace(tzinfo=None)).days
                            r_score = 1.0 / (1.0 + (max(0, days_old) / 30.0))
                    except: pass

                # Combine scores
                s_score = float(norm_semantic[i])
                final_score = (alpha * s_score) + (beta * r_score)
                
                doc_copy = doc.copy()
                doc_copy["_semantic_relevance"] = s_score
                doc_copy["_recency_boost"] = r_score
                doc_copy["_hybrid_score"] = final_score
                reranked_results.append(doc_copy)

            # [v7.1] Re-append remaining docs with baseline scores
            for doc in remaining_docs:
                doc_copy = doc.copy()
                doc_copy["_hybrid_score"] = (doc.get("similarity", 0.1) * alpha)
                reranked_results.append(doc_copy)

            # 4. Sort by final score descending
            reranked_results.sort(key=lambda x: x.get("_hybrid_score", 0), reverse=True)
            
            logger.info(f"[OK] Reranked {len(documents)} docs using Hybrid Weighting (α={alpha}, β={beta})")
            return reranked_results

        except Exception as e:
            logger.error(f"Reranking execution failed: {e}")
            return documents

    async def rerank_remote(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """[v6.0] Call remote Reranker service (Dockerized Cloud Instance)."""
        if not self._remote_url:
            return documents
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "query": query,
                    "documents": [{"content": d.get("content", ""), "id": d.get("id")} for d in documents]
                }
                response = await client.post(f"{self._remote_url}/rerank", json=payload)
                if response.status_code == 200:
                    ranked_ids = response.json().get("results", [])
                    # Re-order documents based on ranked IDs from remote service
                    id_map = {d.get("id"): d for d in documents}
                    return [id_map[rid] for rid in ranked_ids if rid in id_map]
                else:
                    logger.warning(f"Remote Reranker failed ({response.status_code}): {response.text}")
                    return documents
        except Exception as e:
            logger.error(f"Remote Reranker request failed: {e}")
            return documents
        
        return documents # Total fallback

reranker = RerankerService()
