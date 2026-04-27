"""
Embedder Service - Vector Embedding Generation
Purpose: Generate 1536-dimensional embeddings using Gemini API
Usage: Called by ingest.py and rag.py for semantic search
"""

import logging
from typing import List, Optional, Any
from app.core.gemini import gemini_client, types

logger = logging.getLogger("cortex.embedder")


async def generate_embedding(text: str, task_type: str = "retrieval_document", dimensionality: Optional[int] = 1536, client: Any = None) -> Optional[List[float]]:
    """
    Generate vector embedding for given text using Gemini
    
    Args:
        text: Input text to embed
        task_type: Task type for embedding
        dimensionality: Output dimension
        client: Optional transient Gemini client
    
    Returns:
        List of floats, or None if generation fails
    """
    if not text or not text.strip():
        logger.warning("[WARN] Empty text provided for embedding")
        return None
    
    try:
        # Use provided client or fallback to global gemini_client
        target_client = client or gemini_client
        
        if not target_client:
            logger.error("[ERROR] No Gemini client available for embedding")
            return None

        # [v4.1 - v4.2 Resilience] Retry loop for 429 errors with Exponential Backoff
        # [v4.3 Fix] Using gemini-embedding-2-preview (Output dimension 1536 requested)
        models_to_try = ["gemini-embedding-2-preview"]
        backoff_delays = [0, 1.0, 2.0] # 0, 1s, 2s
        
        last_err = None
        for model_id in models_to_try:
            for delay in backoff_delays:
                if delay > 0:
                    import asyncio
                    import random
                    await asyncio.sleep(delay + random.uniform(0, 0.3))
                    logger.info(f"Retrying embedding {model_id} after {delay}s backoff...")

                try:
                    # Generate embedding using google.genai SDK
                    result = await target_client.aio.models.embed_content(
                        model=model_id,
                        contents=text,
                        config=types.EmbedContentConfig(
                            task_type="RETRIEVAL_DOCUMENT" if task_type == "retrieval_document" else "RETRIEVAL_QUERY",
                            title="Cortex Memory" if task_type == "retrieval_document" else None,
                            output_dimensionality=dimensionality
                        )
                    )

                    if result.embeddings and len(result.embeddings) > 0:
                        embedding = result.embeddings[0].values
                        if dimensionality and len(embedding) != dimensionality:
                            logger.warning(f"[WARN] Unexpected embedding dimension: {len(embedding)} (expected {dimensionality})")
                        logger.info(f"[OK] Generated embedding (len={len(text)}, dim={len(embedding)})")
                        return list(embedding)
                    
                    logger.error(f"[ERROR] No embeddings returned from {model_id}")

                except Exception as e:
                    last_err = e
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        logger.warning(f"Embedding model {model_id} exhausted (429) at delay {delay}s.")
                        continue # Try next backoff
                    else:
                        break # Critical error
            
            # If all backoffs for this model failed, try next model in loop
            continue
        
        if last_err:
            logger.error(f"[ERROR] Failed to generate embedding after all retries: {last_err}")
        return None

    except Exception as e:
        logger.error(f"[ERROR] Fatal error in generate_embedding: {e}")
        return None


async def batch_generate_embeddings(texts: List[str], task_type: str = "retrieval_document", dimensionality: int = 1536) -> List[Optional[List[float]]]:
    """
    Generate embeddings for multiple texts
    """
    embeddings = []
    
    for i, text in enumerate(texts):
        embedding = await generate_embedding(text, task_type, dimensionality)
        embeddings.append(embedding)
        
        # Rate limiting: Gemini free tier allows 1500 requests/day
        # Add small delay to avoid hitting rate limits
        if i < len(texts) - 1:
            import asyncio
            await asyncio.sleep(0.1)
    
    logger.info(f"[OK] Batch generated {len([e for e in embeddings if e])} / {len(texts)} embeddings")
    return embeddings
