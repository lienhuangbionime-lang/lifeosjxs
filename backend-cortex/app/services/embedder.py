"""
Embedder Service - Vector Embedding Generation
Purpose: Generate 3072-dimensional embeddings using Gemini API
Usage: Called by ingest.py and rag.py for semantic search
"""

import logging
from typing import List, Optional
from app.core.gemini import get_model
import google.generativeai as genai

logger = logging.getLogger("cortex.embedder")


async def generate_embedding(text: str, task_type: str = "retrieval_document") -> Optional[List[float]]:
    """
    Generate vector embedding for given text using Gemini
    
    Args:
        text: Input text to embed
        task_type: Task type for embedding (retrieval_document, retrieval_query, semantic_similarity)
    
    Returns:
        List of 3072 floats, or None if generation fails
    """
    if not text or not text.strip():
        logger.warning("[WARN] Empty text provided for embedding")
        return None
    
    try:
        # Check if Gemini is configured
        model_config = get_model("fast")
        if not model_config.get("configured"):
            logger.error("[ERROR] Gemini API not configured")
            return None
        
        # Generate embedding using stable high-dimension model
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type=task_type,
            title="Cortex Memory" if task_type == "retrieval_document" else None,
            output_dimensionality=3072
        )
        
        embedding = result['embedding']
        
        # Verify dimension
        if len(embedding) != 3072:
            logger.warning(f"[WARN] Unexpected embedding dimension: {len(embedding)} (expected 3072)")
        
        logger.info(f"[OK] Generated embedding for text (length: {len(text)}, dims: {len(embedding)})")
        return embedding
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to generate embedding: {e}")
        return None


async def batch_generate_embeddings(texts: List[str], task_type: str = "retrieval_document") -> List[Optional[List[float]]]:
    """
    Generate embeddings for multiple texts
    
    Args:
        texts: List of input texts
        task_type: Task type for embedding
    
    Returns:
        List of embeddings (same length as input, None for failed items)
    """
    embeddings = []
    
    for i, text in enumerate(texts):
        embedding = await generate_embedding(text, task_type)
        embeddings.append(embedding)
        
        # Rate limiting: Gemini free tier allows 1500 requests/day
        # Add small delay to avoid hitting rate limits
        if i < len(texts) - 1:
            import asyncio
            await asyncio.sleep(0.1)
    
    logger.info(f"[OK] Batch generated {len([e for e in embeddings if e])} / {len(texts)} embeddings")
    return embeddings
