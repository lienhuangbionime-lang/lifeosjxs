"""
Embedder Service - Vector Embedding Generation
Purpose: Generate 3072-dimensional embeddings using Gemini API
Usage: Called by ingest.py and rag.py for semantic search
"""

import logging
from typing import List, Optional
from app.core.gemini import gemini_client, types

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
        if not gemini_client:
            logger.error("[ERROR] gemini_client not configured")
            return None

        # Generate embedding using google.genai SDK
        # text-embedding-004 deprecated 2026-01-14, replaced by gemini-embedding-001
        result = await gemini_client.aio.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT" if task_type == "retrieval_document" else "RETRIEVAL_QUERY",
                title="Cortex Memory" if task_type == "retrieval_document" else None,
                output_dimensionality=3072
            )
        )

        if not result.embeddings or len(result.embeddings) == 0:
            logger.error("[ERROR] No embeddings returned")
            return None

        embedding = result.embeddings[0].values

        if len(embedding) != 3072:
            logger.warning(f"[WARN] Unexpected embedding dimension: {len(embedding)} (expected 3072)")

        logger.info(f"[OK] Generated embedding (len={len(text)}, dims={len(embedding)})")
        return list(embedding)

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
