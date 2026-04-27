import os
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.core.gemini import get_model, gemini_client, types
from app.services.embedder import generate_embedding
from app.services.reranker import reranker

import math

logger = logging.getLogger("cortex.rag_service")

def calculate_decay_score(raw_similarity: float, access_count: int, last_accessed_str: str, current_time: Optional[datetime] = None) -> float:
    """
    LifeOS Knowledge Decay Formula (Phase E)
    Adjusts the raw pgvector cosine similarity score based on time elapsed and retrieval frequency.
    """
    if current_time is None:
        current_time = datetime.now()
        
    base_half_life_days = 30
    # Every access extends the half-life by 7 days, up to a year
    effective_half_life = min(365, base_half_life_days + ((access_count or 0) * 7))
    
    days_elapsed = 0
    if last_accessed_str:
        try:
            # Parse typical Postgres ISO 8601 strings
            last_accessed_at = datetime.fromisoformat(last_accessed_str.replace('Z', '+00:00'))
            # Calculate delta (Ensure timezone naive math for simplicity if needed, or matched tz)
            curr_utc = datetime.now().astimezone() 
            delta = curr_utc - last_accessed_at
            days_elapsed = max(0, delta.total_seconds() / 86400.0)
        except Exception as e:
            logger.warning(f"Could not parse last_accessed_str '{last_accessed_str}': {e}")
            
    # Exponential decay formula: N(t) = N0 * (1/2)^(t/h)
    decay_multiplier = math.pow(0.5, days_elapsed / effective_half_life)
    
    # Access Frequency Boost (+0.05 max to similarity)
    frequency_boost = min(0.05, float(access_count or 0) * 0.005)
    
    final_score = float((raw_similarity * decay_multiplier) + frequency_boost)
    return max(0.0, min(1.0, final_score))

class Memory:
    """Standardized memory data structure for the system."""
    def __init__(self, id: str, content: str, date: str, similarity: float, metadata: Optional[Dict] = None, ai_insights: Optional[str] = None):
        self.id = id
        # [v4.3 Mapping Fix] Prioritize ai_insights if content is empty
        self.raw_content = content
        self.ai_insights = ai_insights
        self.content = ai_insights if (ai_insights and not content) else (content or "")
        self.date = date
        self.similarity = similarity
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "ai_insights": self.ai_insights,
            "date": self.date,
            "similarity": self.similarity,
            "metadata": self.metadata
        }

class UnifiedRAGService:
    """
    [PROTOCOL: ACTIVE INTELLIGENCE]
    Unified RAG Service v3.8.5 - v4.3
    Consolidates atomic memory retrieval (hybrid search) and document-track knowledge.
    """
    def __init__(self):
        self.enabled = bool(supabase)
        if not self.enabled:
            logger.warning("UnifiedRAGService disabled: Supabase not configured.")

    async def hybrid_search_memories(
        self, 
        query: str, 
        limit: int = 5, 
        similarity_threshold: float = 0.5,
        client: Any = None
    ) -> List[Memory]:
        """
        Hybrid search for 'memories' table: Vector + Fallback (Keyword/Date).
        """
        if not self.enabled:
            return []

        try:
            # 1. Vector Search
            query_embedding = await generate_embedding(query, task_type="retrieval_query", client=client)
            if not query_embedding:
                return await self._fallback_search(query, limit)

            # We fetch more than we need so we can re-sort them after applying the Decay Formula
            rpc_params = {
                "query_embedding": query_embedding,
                "match_threshold": similarity_threshold,
                "match_count": limit * 2
            }
            
            # [v4.3] match_memories RPC usually returns fixed columns. 
            # If it misses ai_insights, we might need a follow-up select or update the RPC.
            response = supabase.rpc("match_memories", rpc_params).execute()
            results = response.data

            # 2. Process Vector Results & Apply Knowledge Decay Scoring
            memories = []
            if results:
                processed_results = []
                for item in results:
                    raw_sim = item.get("similarity", 0.0)
                    access_count = item.get("access_count", 0)
                    last_accessed = item.get("last_accessed_at")
                    
                    # Apply Phase E Decay Formula
                    dynamic_sim = calculate_decay_score(raw_sim, access_count, last_accessed)
                    item["original_similarity"] = raw_sim
                    item["similarity"] = dynamic_sim
                    processed_results.append(item)
                    
                # Re-sort descending based on the new Decay-adjusted similarity
                processed_results.sort(key=lambda x: x['similarity'], reverse=True)
                
                # Take the top requested limit
                final_results = processed_results[:limit]
                
                for item in final_results:
                    # [v4.3 Diagnostic] If RPC doesn't return ai_insights, we attempt to use what's there
                    mem = Memory(
                        id=item.get("id"),
                        content=item.get("content"),
                        ai_insights=item.get("ai_insights"),
                        date=item.get("date") or item.get("metadata", {}).get("date", "unknown"),
                        similarity=item.get("similarity", 0.0),
                        metadata=item.get("metadata", {})
                    )
                    memories.append(mem)
                    
                # Fire-and-forget RPC call to increment access counts
                try:
                    memory_ids = [m.id for m in memories]
                    if memory_ids:
                        supabase.rpc("increment_memory_access", {"memory_ids": memory_ids}).execute()
                        logger.info(f"Knowledge Decay: Bumped access_count for {len(memory_ids)} memories.")
                except Exception as rpc_e:
                    logger.warning(f"Failed to increment memory access: {rpc_e}")
                    
                return memories

            # 3. Fallback to Keyword/Date if vector returns nothing
            return await self._fallback_search(query, limit)

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def search_and_rerank(
        self, 
        query: str, 
        recall_limit: int = 40, 
        top_k: int = 10,
        alpha: float = 0.7,
        beta: float = 0.3,
        client: Any = None
    ) -> List[Dict[str, Any]]:
        """
        Two-Stage RAG Entrance:
        1. Recall (Broad vector search)
        2. Rerank (HuggingFace Hybrid Semantic-Temporal Reranking)
        """
        if not self.enabled: return []

        try:
            # 1. Recall Phase (High recall limit)
            candidates = await self.hybrid_search_memories(
                query, 
                limit=recall_limit, 
                similarity_threshold=0.3, 
                client=client
            )
            if not candidates:
                return []
            
            # Convert Memory objects to dictionaries for the reranker
            candidate_dicts = [m.to_dict() for m in candidates]

            # 2. Rerank Phase
            reranked = reranker.rerank(
                query=query, 
                documents=candidate_dicts,
                alpha=alpha,
                beta=beta
            )

            # Return top-K after reranking
            return reranked[:top_k]

        except Exception as e:
            logger.error(f"Search and rerank failed: {e}")
            return []

    async def search_documents(self, query: str, limit: int = 5, path_prefix: Optional[str] = None) -> List[Dict]:
        """Search 'documents' table for external knowledge with Phase E Knowledge Decay."""
        if not self.enabled: return []
        
        try:
            query_embedding = await generate_embedding(query, task_type="retrieval_query")
            if not query_embedding: return []

            # We fetch more than we need so we can re-sort them after applying the Decay Formula
            rpc_params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.3, 
                "match_count": limit * 2 
            }
            
            response = supabase.rpc("match_documents", rpc_params).execute()
            docs = response.data or []
            
            if not docs:
                return []
                
            # Filter by path_prefix if provided (metadata->>source)
            if path_prefix:
                docs = [d for d in docs if str(d.get("metadata", {}).get("source", "")).startswith(path_prefix)]

            # --- Phase E: Knowledge Decay Scoring ---
            processed_docs = []
            for d in docs:
                raw_sim = d.get('similarity', 0.0)
                access_count = d.get('access_count', 0)
                last_accessed = d.get('last_accessed_at')
                
                # Re-calculate similarity score accounting for Memory Decay
                dynamic_sim = calculate_decay_score(raw_sim, access_count, last_accessed)
                d['original_similarity'] = raw_sim
                d['similarity'] = dynamic_sim
                processed_docs.append(d)
                
            # Re-sort descending based on the new Decay-adjusted similarity
            processed_docs.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Take the top requested limit
            final_selection = processed_docs[:limit]
            
            if final_selection:
                # Fire-and-forget RPC call to increment access counts and update last_accessed_at
                try:
                    doc_ids = [d['id'] for d in final_selection if 'id' in d]
                    if doc_ids:
                        supabase.rpc("increment_document_access", {"doc_ids": doc_ids}).execute()
                        logger.info(f"Knowledge Decay: Bumped access_count for {len(doc_ids)} documents.")
                except Exception as rpc_e:
                    logger.warning(f"Failed to increment document access: {rpc_e}")
                    
            return final_selection
            
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return []

    async def search_memory_embeddings(self, query: str, limit: int = 5, path_prefix: Optional[str] = "memory/") -> List[Dict]:
        """Search 'memory_embeddings' table (1536 dim) for prioritized personal content."""
        if not self.enabled: return []
        
        try:
            # Table uses 1536 dim (v2 Preview)
            query_embedding = await generate_embedding(query, dimensionality=1536, task_type="retrieval_query")
            if not query_embedding: return []

            rpc_params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.4,
                "match_count": limit * 2
            }
            
            # This RPC must be created in Supabase (see implementation_plan.md)
            response = supabase.rpc("match_memory_embeddings", rpc_params).execute()
            results = response.data or []
            
            if not results:
                return []
                
            # Filter by path_prefix logic (CRITICAL PRIORITY: files in memory/ directory)
            if path_prefix:
                # We normalize the prefix and the source for comparison
                results = [r for r in results if path_prefix.lower() in str(r.get("metadata", {}).get("source", "")).lower()]
            
            # Apply Decay logic (similar to memories/documents)
            processed = []
            for r in results:
                r["similarity"] = calculate_decay_score(r.get("similarity", 0.0), r.get("access_count", 0), r.get("last_accessed_at"))
                processed.append(r)
            
            processed.sort(key=lambda x: x["similarity"], reverse=True)
            final_results = processed[:limit]
            
            # Increment access counts
            try:
                ids = [r["id"] for r in final_results]
                if ids:
                    supabase.rpc("increment_memory_embeddings_access", {"ids": ids}).execute()
            except Exception as rpc_e:
                logger.warning(f"Failed to increment memory_embeddings access: {rpc_e}")
                
            return final_results
        except Exception as e:
            logger.error(f"Memory embeddings search failed: {e}")
            return []

    async def _fallback_search(self, query: str, limit: int) -> List[Memory]:
        """Simple keyword and date fallback logic."""
        logger.info(f"RAG Fallback triggered for: '{query}'")
        
        # Detect date patterns (YYYY-MM-DD or MM/DD)
        date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})|(\d{1,2})[-/](\d{1,2})', query)
        
        # Select both content and ai_insights for mapping
        query_builder = supabase.table("memories").select("id,content,ai_insights,date,metadata")
        
        if date_match:
            groups = date_match.groups()
            if groups[3] and groups[4]: # MM/DD
                m, d = groups[3].zfill(2), groups[4].zfill(2)
                curr_y = datetime.now().year
                query_builder = query_builder.in_("date", [f"{curr_y}-{m}-{d}", f"{curr_y-1}-{m}-{d}"])
            elif groups[0] and groups[1] and groups[2]: # YYYY-MM-DD
                y, m, d = groups[0], groups[1].zfill(2), groups[2].zfill(2)
                query_builder = query_builder.eq("date", f"{y}-{m}-{d}")
        else:
            # Fallback search both columns
            query_builder = query_builder.or_(f"content.ilike.%{query}%,ai_insights.ilike.%{query}%")

        res = query_builder.limit(limit).execute()
        
        memories = []
        for item in (res.data or []):
            memories.append(Memory(
                id=item.get("id"),
                content=item.get("content"),
                ai_insights=item.get("ai_insights"),
                date=item.get("date", "unknown"),
                similarity=0.9, # High score for direct match
                metadata=item.get("metadata", {})
            ))
        return memories

    async def unified_search(self, question: str, limit: int = 5, path_prefix: Optional[str] = "memory/") -> Dict[str, str]:
        """
        The Master Search Entrance.
        Retrieves from:
        1. memories (Daily Log / Chat Intake)
        2. memory_embeddings (Vectorized Markdown Files - Prioritized)
        3. documents (bulk knowledge)
        """
        # [v7.1] Forced Path Filtering for Diary/Reflection keywords
        diary_keywords = ["日記", "反思", "心路歷程", "diary", "reflection", "personal journey"]
        if any(kw in question.lower() for kw in diary_keywords):
            logger.info(f"🔮 Diary keyword detected. Forcing path_prefix='memory/' for retrieval.")
            path_prefix = "memory/"
        
        # [PRORITY TRACK] Search vectorized markdown files (memory_embeddings)
        embedded_memories = await self.search_memory_embeddings(question, limit=limit, path_prefix=path_prefix)
        
        # [SYNC TRACK] Reranking-First Search (Atomic Daily Memories)
        memories_results = await self.search_and_rerank(question, recall_limit=40, top_k=limit)
        
        # [KNOWLEDGE TRACK] Search documents separately
        documents = await self.search_documents(question, limit=limit)

        # Build Contexts
        # 1. Embedded memories (prioritized by instruction but here they get their own block)
        emb_text = "\n\n".join([f"[{m.get('metadata', {}).get('file_name', 'File')}] {m.get('content', '')}" for m in embedded_memories])
        
        # 2. Daily Log memories
        mem_text = "\n\n".join([f"[{m.get('date', 'unknown')}] {m.get('content', '')}" for m in memories_results])
        
        # 3. Documents
        doc_text = "\n\n".join([f"[{d.get('title', 'Doc')}] {d.get('content', '')}" for d in documents])

        # Combine embedded and daily memories for the 'memories' key to ensure AI sees them as one prioritize track
        combined_memories = f"--- [Vectorized Workspace Files (Prioritized)] ---\n{emb_text}\n\n--- [Daily Intake Logs] ---\n{mem_text}"

        return {
            "memories": combined_memories.strip(),
            "documents": doc_text
        }

    async def ingest_text(self, text: str, meta: Dict[str, Any] = {}, target: str = "documents") -> int:
        """Ingest raw text into the specified table."""
        if not self.enabled: return 0
        
        try:
            embedding = await generate_embedding(text, dimensionality=1536)
            payload = {
                "content": text,
                "metadata": meta,
                "created_at": datetime.now().isoformat()
            }
            
            if target == "documents":
                payload["title"] = meta.get("title", f"Note {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                payload["doc_type"] = meta.get("type", "webpage")
                if embedding:
                    payload["embedding"] = embedding
            elif target == "memories":
                # memories table needs date field
                payload["date"] = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
                payload["category"] = meta.get("category", "Chat")
                payload["tags"] = meta.get("tags", [])
                payload["is_ai"] = meta.get("is_ai", True)
                # Try with embedding first, fall back without
                if embedding:
                    try:
                        payload_embed = {**payload, "embedding": embedding}
                        from app.core.database import safe_write
                        safe_write(supabase.table(target), payload_embed, operation_type="insert")
                        logger.info(f"[Memory Write] Saved with embedding: {text[:60]}")
                        return 1
                    except Exception:
                        logger.warning("[Memory Write] Embedding insert failed, falling back to text-only insert.")
            
            from app.core.database import safe_write
            safe_write(supabase.table(target), payload, operation_type="insert")
            logger.info(f"[Memory Write] Saved (text-only): {text[:60]}")
            return 1
        except Exception as e:
            logger.error(f"Text ingest failed for target {target}: {e}")
            return 0

    async def ingest_file(self, file: Any, target: str = "documents") -> int:
        """
        [NEW] Ingest a file into the knowledge base.
        If it's an image, use Gemini Vision to interpret it.
        """
        if not self.enabled: return 0
        
        try:
            filename = file.filename
            content_type = file.content_type
            data = await file.read()
            
            # 1. Handle Multimodal Content (Images, PDFs)
            multimodal_mimes = ["image/", "application/pdf"]
            if any(content_type.startswith(m) for m in multimodal_mimes):
                logger.info(f"🔮 Multimodal content detected: {filename} ({content_type}). Using Gemini for interpretation...")
                from app.core.gemini import multimodal_interpret
                
                interpretation = await multimodal_interpret(data, content_type)
                text_content = f"### Multimodal Interpretation: {filename}\n\n{interpretation}"
                logger.info(f"[OK] Gemini generated interpretation via Safe Failover.")
            else:
                # 2. Handle Text/PDF (Simplified for now - Title only)
                # TODO: Implement full PDF/Doc parsing
                text_content = f"Document File: {filename}\nContent Type: {content_type}\n(Binary content stored, but text extraction pending implementation)"

            # 3. Ingest the generated text description
            return await self.ingest_text(
                text=text_content,
                meta={
                    "source": "file_upload",
                    "filename": filename,
                    "content_type": content_type,
                    "title": f"Upload: {filename}"
                },
                target=target
            )
            
        except Exception as e:
            logger.error(f"File ingest failed: {e}")
            return 0

# Singleton instance
rag_service = UnifiedRAGService()
