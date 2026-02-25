
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
        response = db.table("memories").select("id,date,content,ai_insights,tags,mood,focus,energy").order("date", desc=True).limit(limit).execute()
        memories = response.data or []

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
async def get_node_context(http_request: Request, label: str):
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

        from app.services.embedder import generate_embedding
        
        # 1. Generate embedding for the label
        query_vector = await generate_embedding(label, task_type="retrieval_query")

        related_memories = []

        # 2. Vector search (only if embedding succeeded)
        if query_vector:
            rpc_params = {
                "query_embedding": query_vector,
                "match_threshold": 0.3,
                "match_count": 10
            }
            response = db.rpc("match_memories", rpc_params).execute()
            rpc_results = response.data or []
            
            # Hydrate full memory data since RPC might return null content / no ai_insights
            if rpc_results:
                matched_ids = [m["id"] for m in rpc_results]
                hydrated = db.table("memories") \
                    .select("id,date,content,ai_insights,mood,focus,energy") \
                    .in_("id", matched_ids) \
                    .execute()
                
                # Create a lookup mapping and preserve RPC similarity order
                mem_map = {m["id"]: m for m in (hydrated.data or [])}
                
                for rpc_mem in rpc_results:
                    m_id = rpc_mem["id"]
                    if m_id in mem_map:
                        full_mem = mem_map[m_id]
                        # Prefer ai_insights, fallback to content
                        content = full_mem.get("ai_insights") or full_mem.get("content") or ""
                        
                        related_memories.append({
                            "id": m_id,
                            "date": full_mem.get("date") or rpc_mem.get("metadata", {}).get("date", "Unknown"),
                            "content": content,
                            "mood": full_mem.get("mood"),
                            "focus": full_mem.get("focus"),
                            "energy": full_mem.get("energy"),
                            "matchReason": {"type": "semantic", "label": f"Semantic Match ({rpc_mem.get('similarity', 0):.2f})"}
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
            related_memories = resp.data or []
            for mem in related_memories:
                mem["matchReason"] = {"type": "keyword", "label": "Keyword Match"}

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
            return resp.data or []
        except:
            return []

@router.get("/node/{label}/insight")
async def get_node_insight(http_request: Request, label: str):
    """
    Generate an AI-driven observation based on the context of a node.
    Synthesizes why this label is significant across different memories.
    """
    db = get_request_client(http_request)
    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        # 1. Fetch related context first
        memories = await get_node_context(http_request, label)
        if not memories or isinstance(memories, dict): # Check for error dict
             return {"insight": "此節點尚無足夠的上下文供分析。"}

        # 2. Prepare context for Gemini (Increased to 10 for better synthesis)
        context_snippets = "\n".join([f"- [{m.get('date')}] {m.get('content')[:300]}..." for m in memories[:10]])
        
        import re
        if re.match(r'^\d{4}-\d{2}-\d{2}$', label):
            sys_prompt = """You are the LifeOS Insights Engine. 
Review the provided journal entry for the date '{label}'. 
Generate a short, insightful response in Traditional Chinese summarizing the day.
"""
        else:
            sys_prompt = f"""You are the LifeOS Project Historian & Data Organizer.
Review the provided context about '{label}'. 
Your goal is to ORGANIZE and SYNTHESIZE the data into a high-signal brief.

STRUCTURE:
1. **主題與趨勢** (Core themes/patterns)
2. **關鍵里程碑** (Highlights or progress noted)
3. **現況觀測** (A sharp observation on the current state)

FORMAT:
- Use Markdown.
- Use point form.
- Be observational, not generic.
- Keep it under 150 words.
- Language: Traditional Chinese.
"""
        
        from app.core.gemini import gemini_client, get_model, types
        
        model_conf = get_model("fast")
        response = await gemini_client.aio.models.generate_content(
            model=model_conf["model"],
            contents=f"CONTEXT FOR '{label}':\n{context_snippets}",
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                temperature=0.4 # Reduced for more factual organization
            )
        )
        
        return {"insight": response.text.strip()}

    except Exception as e:
        logger.error(f"Insight Generation Error ({label}): {e}")
        return {"insight": "無法產生語意分析。"}
