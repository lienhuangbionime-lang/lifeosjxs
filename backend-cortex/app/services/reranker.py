
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
import numpy as np
from sentence_transformers import CrossEncoder

logger = logging.getLogger("cortex.reranker")

class RerankerService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RerankerService, cls).__new__(cls)
        return cls._instance

    def initialize(self, model_id: str = "BAAI/bge-reranker-v2-m3"):
        if self._model is None:
            logger.info(f"Loading HuggingFace Reranker model: {model_id}...")
            try:
                self._model = CrossEncoder(model_id)
                logger.info("[OK] Reranker model loaded successfully.")
            except Exception as e:
                logger.error(f"[ERROR] Failed to load reranker model: {e}")
                self._model = None

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
                logger.warning("Reranker not initialized, returning original order.")
                return documents

        try:
            # 1. Get Semantic Scores from Cross-Encoder
            pairs = [[query, doc.get("content", "")] for doc in documents]
            semantic_scores = self._model.predict(pairs)
            
            # Normalize semantic scores to [0, 1] range (sigmoid-like)
            # bge-reranker scores are typically raw logits, we can use a simple normalization or sigmoid
            def sigmoid(x):
                return 1 / (1 + np.exp(-x))
            
            norm_semantic = sigmoid(semantic_scores)

            # 2. Calculate Recency Scores
            now = datetime.now()
            recency_scores = []
            
            for doc in documents:
                created_at_str = doc.get("created_at") or doc.get("date")
                if not created_at_str:
                    recency_scores.append(0.5) # Neutral score for missing date
                    continue
                
                try:
                    # Generic parser for ISO or YYYY-MM-DD
                    if isinstance(created_at_str, str):
                        if "T" in created_at_str:
                            dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        else:
                            dt = datetime.strptime(created_at_str, "%Y-%m-%d")
                    else:
                        dt = now # Fallback
                        
                    days_old = (now - dt.replace(tzinfo=None)).days
                    # Temporal decay: 1.0 for today, 0.5 for 30 days, 0.1 for a year
                    # Simple decay function: 1 / (1 + days/30)
                    decay = 1.0 / (1.0 + (max(0, days_old) / 30.0))
                    recency_scores.append(decay)
                except Exception as de:
                    logger.warning(f"Date parsing failed for {created_at_str}: {de}")
                    recency_scores.append(0.5)

            # 3. Combine scores
            reranked_results = []
            for i, doc in enumerate(documents):
                s_score = float(norm_semantic[i])
                r_score = float(recency_scores[i])
                final_score = (alpha * s_score) + (beta * r_score)
                
                # Clone doc and attach scores
                doc_copy = doc.copy()
                doc_copy["_semantic_relevance"] = s_score
                doc_copy["_recency_boost"] = r_score
                doc_copy["_hybrid_score"] = final_score
                
                reranked_results.append(doc_copy)

            # 4. Sort by final score descending
            reranked_results.sort(key=lambda x: x["_hybrid_score"], reverse=True)
            
            logger.info(f"[OK] Reranked {len(documents)} docs using Hybrid Weighting (α={alpha}, β={beta})")
            return reranked_results

        except Exception as e:
            logger.error(f"Reranking execution failed: {e}")
            return documents

reranker = RerankerService()
