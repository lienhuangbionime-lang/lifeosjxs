import logging
import asyncio
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS

logger = logging.getLogger("cortex.search")

async def search_web(query: str, limit: int = 5, archive: bool = False) -> List[Dict[str, Any]]:
    """
    Performs a web search using DuckDuckGo.
    This provides LifeOS with external information retrieval capabilities.
    If archive is True, results are stored in the documents table.
    """
    logger.info(f"[SEARCH] Querying web for: '{query}'")
    
    try:
        # DDGS is synchronous but we can run it in a thread pool to avoid blocking
        def sync_search():
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=limit)
                return list(results)
        
        # Offload to thread for async hygiene
        results = await asyncio.to_thread(sync_search)
        
        logger.info(f"[OK] Found {len(results)} web results for: '{query}'")
        
        # Archive top results to documents if requested
        if archive and results:
            try:
                from app.services.rag_service import rag_service
                for res in results[:2]: # Archive top 2 results
                    # Fire and forget background task
                    asyncio.create_task(rag_service.ingest_text(
                        text=res.get('body', ''),
                        meta={
                            "title": res.get('title'),
                            "url": res.get('href'),
                            "source": "web_search"
                        },
                        target="documents"
                    ))
                logger.info(f"[SEARCH] Background archiving triggered for top results.")
            except Exception as ae:
                logger.warning(f"[WARN] Failed to archive search results: {ae}")
                
        return results
    except Exception as e:
        logger.error(f"[ERROR] Web search failed: {e}")
        return []

def format_search_results(results: List[Dict[str, Any]]) -> str:
    """Formats search results for injection into AI prompt."""
    if not results:
        return "No web results found."
    
    lines = ["## Web Search Results\n"]
    for i, res in enumerate(results, 1):
        lines.append(f"{i}. **{res.get('title')}**")
        lines.append(f"   Source: {res.get('href')}")
        lines.append(f"   Snippet: {res.get('body')}\n")
    
    return "\n".join(lines)
