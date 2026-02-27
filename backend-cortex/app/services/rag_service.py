import os
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.core.gemini import get_model, gemini_client
from app.services.embedder import generate_embedding

logger = logging.getLogger("cortex.rag_service")

class Memory:
    """Standardized memory data structure for the system."""
    def __init__(self, id: str, content: str, date: str, similarity: float, metadata: Optional[Dict] = None):
        self.id = id
        self.content = content
        self.date = date
        self.similarity = similarity
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "date": self.date,
            "similarity": self.similarity,
            "metadata": self.metadata
        }

class UnifiedRAGService:
    """
    [PROTOCOL: ACTIVE INTELLIGENCE]
    Unified RAG Service v3.8.5
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
        similarity_threshold: float = 0.5
    ) -> List[Memory]:
        """
        Hybrid search for 'memories' table: Vector + Fallback (Keyword/Date).
        Optimized for atomic daily entries.
        """
        if not self.enabled:
            return []

        try:
            # 1. Vector Search
            query_embedding = await generate_embedding(query, task_type="retrieval_query")
            if not query_embedding:
                return await self._fallback_search(query, limit)

            rpc_params = {
                "query_embedding": query_embedding,
                "match_threshold": similarity_threshold,
                "match_count": limit
            }
            
            response = supabase.rpc("match_memories", rpc_params).execute()
            results = response.data

            # 2. Process Vector Results
            memories = []
            if results:
                for item in results:
                    mem = Memory(
                        id=item.get("id"),
                        content=item.get("content", ""),
                        date=item.get("metadata", {}).get("date", "unknown"),
                        similarity=item.get("similarity", 0.0),
                        metadata=item.get("metadata", {})
                    )
                    memories.append(mem)
                return memories

            # 3. Fallback to Keyword/Date if vector returns nothing
            return await self._fallback_search(query, limit)

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def _fallback_search(self, query: str, limit: int) -> List[Memory]:
        """Simple keyword and date fallback logic."""
        logger.info(f"RAG Fallback triggered for: '{query}'")
        
        # Detect date patterns (YYYY-MM-DD or MM/DD)
        date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})|(\d{1,2})[-/](\d{1,2})', query)
        
        query_builder = supabase.table("memories").select("*")
        
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
            query_builder = query_builder.ilike("content", f"%{query}%")

        res = query_builder.limit(limit).execute()
        
        memories = []
        for item in (res.data or []):
            memories.append(Memory(
                id=item.get("id"),
                content=item.get("content", ""),
                date=item.get("date", "unknown"),
                similarity=0.9, # High score for direct match
                metadata=item.get("metadata", {})
            ))
        return memories

    async def search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        """Search 'documents' table for external knowledge."""
        if not self.enabled: return []
        
        try:
            query_embedding = await generate_embedding(query, task_type="retrieval_query")
            if not query_embedding: return []

            rpc_params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.3, 
                "match_count": limit
            }
            
            response = supabase.rpc("match_documents", rpc_params).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return []

    async def unified_search(self, question: str, limit: int = 5) -> Dict[str, str]:
        """
        The Master Search Entrance.
        Retrieves from both Memories (Atomic) and Documents (Bulk Knowledge).
        """
        memories = await self.hybrid_search_memories(question, limit=limit)
        documents = await self.search_documents(question, limit=limit)

        mem_text = "\n\n".join([f"[{m.date}] {m.content}" for m in memories])
        doc_text = "\n\n".join([f"[{d.get('title', 'Doc')}] {d.get('content', '')}" for d in documents])

        return {
            "memories": mem_text,
            "documents": doc_text
        }

    async def ingest_text(self, text: str, meta: Dict[str, Any] = {}, target: str = "documents") -> int:
        """Ingest raw text into the specified table."""
        if not self.enabled: return 0
        
        try:
            # Unified Architecture: All tables target 3072 (Gemini Embedding v1)
            embedding = await generate_embedding(text, dimensionality=3072)
            payload = {
                "content": text,
                "metadata": meta,
                "embedding": embedding,
                "created_at": datetime.now().isoformat()
            }
            if target == "documents":
                payload["title"] = meta.get("title", f"Note {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                # Ensure doc_type is set
                payload["doc_type"] = meta.get("type", "webpage")
            
            supabase.table(target).insert(payload).execute()
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
                logger.info(f"[OK] Gemini generated interpretation.")
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
