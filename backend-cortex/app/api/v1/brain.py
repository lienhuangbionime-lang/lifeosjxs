
from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Dict, Any, Optional
import logging
import re
from app.core.database import supabase, get_request_client

router = APIRouter()
logger = logging.getLogger("cortex.brain")

@router.get("/graph")
async def get_brain_graph(http_request: Request, limit: int = 500):
    """
    Generate the Neural Graph from memories.
    Replicates the logic of CoreEngine.parseGraphSeeds (Frontend) but on the backend.
    """
    db = get_request_client(http_request)
    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        # 1. Fetch recent memories
        try:
            response = db.table("memories").select("id,date,content,ai_insights,tags,mood,focus,energy").order("date", desc=True).limit(limit).execute()
            memories = response.data or []
        except Exception as conn_err:
            logger.warning(f"Brain graph: DB connection failed ({conn_err}), returning empty graph.")
            return {"nodes": [], "links": []}

        # 1.5 Fetch Structural Entities
        try:
            resp_proj = db.table("projects").select("id,name,status").in_("status", ["active", "on_hold"]).execute()
            projects = resp_proj.data or []
        except:
            projects = []

        try:
            resp_nodes = db.table("nodes").select("id,label,type,metadata").execute()
            db_nodes = resp_nodes.data or []
        except:
            db_nodes = []

        try:
            resp_edges = db.table("edges").select("source_id,target_id,relation,weight").execute()
            db_edges = resp_edges.data or []
        except:
            db_edges = []

        nodes = {}
        links = {}

        def add_node(id, group, val, raw=None, label=None):
            if id not in nodes:
                nodes[id] = {"id": id, "group": group, "val": val, "label": label or str(id)}
                if raw:
                    nodes[id]["raw"] = raw

        def add_link(source, target, value):
            key = f"{source}-{target}"
            if key not in links:
                links[key] = {"source": source, "target": target, "value": value}
            else:
                links[key]["value"] += value

        # 2. Inject Structural Layer
        for p in projects:
            add_node(p['id'], 'project', 10, raw=p, label=p['name'])
        
        for n in db_nodes:
            group_map = {'tag': 'tag', 'concept': 'concept', 'person': 'person', 'project': 'project', 'tool': 'concept'}
            group = group_map.get(n['type'], 'concept')
            add_node(n['id'], group, 5, raw=n, label=n['label'])

        for e in db_edges:
            if e['source_id'] in nodes and e['target_id'] in nodes:
                add_link(e['source_id'], e['target_id'], e['weight'])

        # 3. Process Memories
        for memory in memories:
            date_id = memory.get("date")
            ai_insights = memory.get("ai_insights")
            raw_content = memory.get("content") or ""
            content = ai_insights if ai_insights else raw_content
            db_tags = memory.get("tags") or []
            
            if not date_id:
                continue

            label_date = date_id
            title_match = re.search(r'^#\s*\[(\d{4}-\d{2}-\d{2})\]', content)
            if title_match:
                label_date = title_match.group(1)

            add_node(date_id, 1, 5, raw=memory, label=label_date)

            # --- Extract Entities from Content ---
            tag_matches = re.findall(r'#([\w\u4e00-\u9fa5.-]+)', content)
            unique_tags = set(tag_matches)
            for t in db_tags:
                unique_tags.add(t.replace("#", ""))
            
            mention_matches = re.findall(r'@([\w\u4e00-\u9fa5.-]+)', content)
            unique_mentions = set(mention_matches)
            
            wiki_matches = re.findall(r'\[\[(.*?)\]\]', content)
            unique_wikis = set(wiki_matches)

            # --- Nodes & Links: Tags ---
            processed_tags = list(unique_tags)
            for tag in processed_tags:
                add_node(tag, 'tag', 3, label=tag)
                add_link(date_id, tag, 1)

            # --- Nodes & Links: Mentions ---
            for person in unique_mentions:
                add_node(person, 'person', 5, label=person)
                add_link(date_id, person, 2)

            # --- Nodes & Links: Concepts ---
            for concept in unique_wikis:
                add_node(concept, 'concept', 4, label=concept)
                add_link(date_id, concept, 2)
                
            for p in projects:
                if p['name'] in content:
                    add_link(date_id, p['id'], 3)

        return {
            "nodes": list(nodes.values()),
            "links": list(links.values())
        }

    except Exception as e:
        logger.error(f"Graph Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/node/{label}/context")
async def get_node_context(http_request: Request, label: str, g_client: Any = None):
    """
    Find semantically related memories for a given brain node.
    Uses vector search to find context beyond strict keyword matches.
    """
    db = get_request_client(http_request)
    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        import re
        # Check if label is a specific date YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', label):
            resp = db.table("memories").select("id,date,content,ai_insights,mood,focus,energy").eq("date", label).execute()
            if resp.data:
                m = resp.data[0]
                content = m.get("ai_insights") or m.get("content") or ""
                return [{
                    "id": m["id"],
                    "date": m.get("date"),
                    "content": content,
                    "mood": m.get("mood"),
                    "focus": m.get("focus"),
                    "energy": m.get("energy"),
                    "matchReason": {"type": "date_match", "label": "Exact Date Match"}
                }]
            return []

        from app.services.rag_service import rag_service
        
        # Use High-Precision Two-Stage RAG with Reranking and Recency Boost
        # Recall 50 candidates, Rerank to top 10
        reranked_results = await rag_service.search_and_rerank(
            query=label,
            recall_limit=50,
            top_k=10,
            alpha=0.6, # Semantic weight
            beta=0.4,  # Recency weight (slightly increased per user request)
            client=g_client
        )

        related_memories = []
        for rpc_mem in reranked_results:
            m_id = rpc_mem["id"]
            # Prefer ai_insights, fallback to content
            content = rpc_mem.get("ai_insights") or rpc_mem.get("content") or ""
            similarity = rpc_mem.get("_hybrid_score", 0.0)
            
            related_memories.append({
                "id": m_id,
                "date": rpc_mem.get("date") or "Unknown",
                "content": content,
                "mood": rpc_mem.get("mood"),
                "focus": rpc_mem.get("focus"),
                "energy": rpc_mem.get("energy"),
                "matchReason": {
                    "type": "neural_hybrid", 
                    "label": f"Neural Match ({similarity:.2f})",
                    "scores": {
                        "semantic": rpc_mem.get("_semantic_relevance", 0.0),
                        "recency": rpc_mem.get("_recency_boost", 0.0)
                    }
                }
            })

        # 3. If no vector results, fallback to keyword search
        if not related_memories:
            logger.info(f"Vector search empty for '{label}', falling back to keyword search")
            # Search both content and ai_insights
            resp = db.table("memories") \
                .select("id,date,content,ai_insights,mood,focus,energy") \
                .or_(f"content.ilike.%{label}%,ai_insights.ilike.%{label}%") \
                .order("date", desc=True) \
                .limit(10) \
                .execute()
            
            for m in (resp.data or []):
                # Standardize fallback schema
                content = m.get("ai_insights") or m.get("content") or ""
                related_memories.append({
                    "id": m["id"],
                    "date": m.get("date") or "Unknown",
                    "content": str(content),
                    "mood": m.get("mood"),
                    "focus": m.get("focus"),
                    "energy": m.get("energy"),
                    "matchReason": {"type": "keyword", "label": "Keyword Match"}
                })

        return related_memories

    except Exception as e:
        logger.error(f"Node Context Error ({label}): {e}")
        try:
            resp = db.table("memories") \
                .select("id,date,content,ai_insights,mood") \
                .or_(f"content.ilike.%{label}%,ai_insights.ilike.%{label}%") \
                .order("date", desc=True) \
                .limit(10) \
                .execute()
            
            transformed = []
            for m in (resp.data or []):
                content = m.get("ai_insights") or m.get("content") or ""
                transformed.append({
                    "id": m["id"],
                    "date": m.get("date") or "Unknown",
                    "content": str(content),
                    "matchReason": {"type": "fallback", "label": "Critical Fallback Match"}
                })
            return transformed
        except:
            return []

@router.get("/node/{label}/insight")
async def get_node_insight(http_request: Request, label: str):
    """
    Generate an AI-driven observation based on the context of a node.
    Synthesizes why this label is significant across different memories.
    """
    from app.core.gemini import get_request_gemini_client, types, safe_generate_content
    
    g_client = get_request_gemini_client(http_request)
    if not g_client:
        logger.warning(f"No Gemini client available for insight: {label}")
        return {"insight": "無法產生語意分析 (未配置 API 金鑰)。"}

    try:
        # 1. Fetch related context first (Pass the client)
        memories = await get_node_context(http_request, label, g_client=g_client)
        if not memories or isinstance(memories, dict): # Check for error dict
             return {"insight": "此節點尚無足夠的上下文供分析。"}

        # 2. Prepare context for Gemini (Increased to 10 for better synthesis)
        snippets = []
        for m in memories[:10]:
            content = m.get('content') or ""
            date = m.get('date') or "Unknown"
            snippets.append(f"- [{date}] {str(content)[:300]}...")
            
        context_snippets = "\n".join(snippets)
        
        import re
        if re.match(r'^\d{4}-\d{2}-\d{2}$', label):
            sys_prompt = f"""You are the LifeOS Insights Engine. 
Review the provided journal entry for the date '{label}'. 
Generate a short, insightful response in Traditional Chinese summarizing the day.
"""
        else:
            sys_prompt = f"""You are the LifeOS Project Historian & Data Organizer.
Review the provided context about '{label}'. 

# Directive
1. **Contextual Honesty**: If the provided context is sparse, irrelevant, or very old, state this clearly and focus on defining the current goal.
2. **Anti-Hallucination**: Do NOT force-link unrelated technical history (like LifeOS v3.0 architecture) to a new specific topic (like a Video Project) just because they share words like 'AI' or 'Project'.
3. **Synthesis**: If specific data is missing, synthesize what is known and provide forward-looking 'seed thoughts' or next steps.

STRUCTURE:
1. **主題與趨勢** (Core themes/patterns)
2. **關鍵里程碑** (Highlights or progress noted; if none for this specific topic, note 'Searching for first milestone...')
3. **現況觀測** (A sharp, honest observation on the current state or data gap)

FORMAT:
- Use Markdown and point form.
- Be observational, not generic.
- Keep it under 150 words.
- Language: Traditional Chinese.
"""
        
        # Use the new v4.1 Safe Failover Protocol
        response = await safe_generate_content(
            client=g_client,
            prefer_mode="fast", # Brain insights are usually satisfied by Flash
            contents=f"CONTEXT FOR '{label}':\n{context_snippets}",
            config=types.GenerateContentConfig(
                temperature=0.4
            ),
            system_instruction=sys_prompt
        )
        
        if not response or not hasattr(response, 'text') or not response.text:
            return {"insight": "無法產生語意分析 (AI 回應為空或被過濾)。"}
            
        return {"insight": response.text.strip()}

    except Exception as e:
        logger.error(f"Insight Generation Error ({label}): {str(e)}")
        # Provide more context in the error for debugging while developing
        return {"insight": f"無法產生語意分析 (系統錯誤: {str(e)[:50]}...)"}
