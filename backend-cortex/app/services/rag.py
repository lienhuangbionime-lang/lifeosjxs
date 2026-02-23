"""
RAG Service - Hybrid Search with Semantic + Filters
Purpose: Retrieve relevant memories using vector similarity and metadata filters
Usage: Called by chat.py to inject context before AI generation
"""

import logging
import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from app.core.database import supabase
from app.services.embedder import generate_embedding

logger = logging.getLogger("cortex.rag")


class Memory:
    """Memory data structure"""
    def __init__(self, id: str, content: str, date: str, similarity: float, metadata: Dict = None):
        self.id = id
        self.content = content
        self.date = date
        self.similarity = similarity
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "date": self.date,
            "similarity": self.similarity,
            "metadata": self.metadata
        }


def load_local_memory(local_path: str) -> Optional[str]:
    """
    Load full content from local JSON file
    
    Args:
        local_path: Relative path to local file (e.g., "2026-02-17.json")
    
    Returns:
        Full content string, or None if file not found
    """
    try:
        file_path = os.path.join("data", "memories", local_path)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # New format: entries array with combined_content
                if "combined_content" in data:
                    return data["combined_content"]
                
                # Legacy format: single content field
                if "ai_processed" in data:
                    return data.get("ai_processed") or data.get("content")
                
                # Fallback
                return data.get("content")
        else:
            logger.warning(f"[WARN] Local file not found: {file_path}")
            return None
    except Exception as e:
        logger.error(f"[ERROR] Failed to load local memory: {e}")
        return None


async def hybrid_search(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 5,
    similarity_threshold: float = 0.5
) -> List[Memory]:
    """
    Hybrid search: Semantic similarity + metadata filters
    
    Args:
        query: Search query text
        filters: Optional filters (date_range, tags, category)
        limit: Maximum number of results
        similarity_threshold: Minimum similarity score (0-1)
    
    Returns:
        List of Memory objects sorted by relevance
    """
    if not supabase:
        logger.error("[ERROR] Supabase not configured")
        return []
    
    try:
        # 1. Generate query embedding
        query_embedding = await generate_embedding(query, task_type="retrieval_query")
        if not query_embedding:
            logger.error("[ERROR] Failed to generate query embedding")
            return []
        
        # 2. Call Supabase RPC function for vector search
        # Note: match_memories function is defined in supabase_init.sql
        rpc_params = {
            "query_embedding": query_embedding,
            "match_threshold": similarity_threshold,
            "match_count": limit * 2  # Fetch more for filtering
        }
        
        response = supabase.rpc("match_memories", rpc_params).execute()
        
        results = response.data
        filtered_results = []
        
        if results:
            for item in results:
                # Apply filters if provided
                if filters and isinstance(filters, dict):
                    # Date range filter
                    if "date_range" in filters:
                        start_date, end_date = filters["date_range"]
                        item_metadata = item.get("metadata") or {}
                        item_date = item_metadata.get("date")
                        if item_date:
                            if not (start_date <= item_date <= end_date):
                                continue
                    
                    # Tags filter
                    if "tags" in filters:
                        required_tags = set(filters["tags"])
                        item_metadata = item.get("metadata") or {}
                        item_tags = set(item_metadata.get("tags", []))
                        if not required_tags.intersection(item_tags):
                            continue
                    
                    # Category filter
                    if "category" in filters:
                        item_metadata = item.get("metadata") or {}
                        if item_metadata.get("category") != filters["category"]:
                            continue
                
                # Load full content from local file
                local_path = item.get("local_path")
                full_content = None
                
                if local_path:
                    full_content = load_local_memory(local_path)
                
                # Fallback to ai_insights if local file not available
                if not full_content:
                    full_content = item.get("ai_insights") or item.get("content") or "[Content unavailable]"
                
                # Create Memory object
                memory = Memory(
                    id=item.get("id"),
                    content=full_content,
                    date=item.get("metadata", {}).get("date", "unknown"),
                    similarity=item.get("similarity", 0.0),
                    metadata=item.get("metadata", {})
                )
                filtered_results.append(memory)
                
                # Stop if we have enough results
                if len(filtered_results) >= limit:
                    break
        
        if not filtered_results:
            logger.info(f"[INFO] Vector search returned no results for query: '{query}'. Falling back to simple keyword/date match.")
            
            # Simple fallback for exact date or keyword matches
            import re
            from datetime import datetime
            
            # Detect patterns like 1/18, 01-18, 2026-01-18
            date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})|(\d{1,2})[-/](\d{1,2})', query)
            
            query_builder = supabase.table("memories").select("*")
            
            if date_match:
                groups = date_match.groups()
                if groups[3] and groups[4]: # MM/DD format
                    m, d = groups[3].zfill(2), groups[4].zfill(2)
                    current_year = datetime.now().year
                    search_dates = [f"{current_year}-{m}-{d}", f"{current_year-1}-{m}-{d}"]
                    logger.info(f"[INFO] Date MM/DD detected: {m}/{d}. Checking years: {search_dates}")
                    query_builder = query_builder.in_("date", search_dates)
                elif groups[0] and groups[1] and groups[2]: # YYYY/MM/DD format
                    y, m, d = groups[0], groups[1].zfill(2), groups[2].zfill(2)
                    search_date = f"{y}-{m}-{d}"
                    query_builder = query_builder.eq("date", search_date)
            else:
                # Direct keyword search in content
                query_builder = query_builder.ilike("content", f"%{query}%")
                
            try:
                res = query_builder.limit(limit).execute()
            except Exception as dbe:
                logger.error(f"[ERROR] Fallback DB query failed: {dbe}")
                res = None
            
            if res and res.data:
                for item in res.data:
                    local_path = item.get("local_path")
                    full_content = None
                    if local_path:
                        full_content = load_local_memory(local_path)
                    
                    if not full_content:
                        full_content = item.get("ai_insights") or item.get("content") or "[Content unavailable]"
                    
                    memory = Memory(
                        id=item.get("id"),
                        content=full_content,
                        date=item.get("date") or "unknown",
                        similarity=0.95, # Artificial high similarity for exact fallback matches
                        metadata=item.get("metadata") or {}
                    )
                    filtered_results.append(memory)
                logger.info(f"[OK] Fallback search found {len(filtered_results)} results")

        return filtered_results
        
    except Exception as e:
        logger.error(f"[ERROR] Hybrid search failed: {e}")
        return []


async def get_recent_memories(days: int = 7, limit: int = 10) -> List[Memory]:
    """
    Get recent memories without semantic search
    
    Args:
        days: Number of days to look back
        limit: Maximum number of results
    
    Returns:
        List of Memory objects sorted by date (newest first)
    """
    if not supabase:
        logger.error("[ERROR] Supabase not configured")
        return []
    
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        
        response = supabase.table("memories") \
            .select("id, local_path, ai_insights, content, date, tags, category") \
            .gte("date", cutoff_date) \
            .order("date", desc=True) \
            .limit(limit) \
            .execute()
        
        # Load full content from local files
        memories = []
        for item in response.data:
            local_path = item.get("local_path")
            full_content = None
            
            if local_path:
                full_content = load_local_memory(local_path)
            
            # Fallback to ai_insights or content field
            if not full_content:
                full_content = item.get("ai_insights") or item.get("content") or "[Content unavailable]"
            
            memories.append(Memory(
                id=item["id"],
                content=full_content,
                date=item["date"],
                similarity=1.0,  # No similarity score for recent fetch
                metadata={"tags": item.get("tags", []), "category": item.get("category")}
            ))
        
        logger.info(f"[OK] Retrieved {len(memories)} recent memories (last {days} days)")
        return memories
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to get recent memories: {e}")
        return []


def format_memories_for_context(memories: List[Memory], max_length: int = 2000) -> str:
    """
    Format memories for injection into chat context
    
    Args:
        memories: List of Memory objects
        max_length: Maximum total character length
    
    Returns:
        Formatted string for prompt injection
    """
    if not memories:
        return ""
    
    context_parts = ["## Relevant Context from Your Memories\n"]
    current_length = len(context_parts[0])
    
    for i, memory in enumerate(memories, 1):
        # Format: Date | Similarity | Content preview
        preview = memory.content[:300] + "..." if len(memory.content) > 300 else memory.content
        entry = f"\n**Memory {i}** ({memory.date}, relevance: {memory.similarity:.2f}):\n{preview}\n"
        
        if current_length + len(entry) > max_length:
            context_parts.append("\n*(Additional memories truncated due to length)*")
            break
        
        context_parts.append(entry)
        current_length += len(entry)
    
    return "".join(context_parts)
