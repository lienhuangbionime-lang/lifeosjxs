
from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Dict, Any, Optional
import logging
import re
from app.core.database import supabase, get_request_client

router = APIRouter()
logger = logging.getLogger("cortex.brain")

@router.get("/context")
async def get_brain_context(http_request: Request):
    """
    Fetch the 'Cloud Brain' shared memory context from Supabase.
    This powers the visual 'Brain Memory' tab in the UI.
    """
    db = get_request_client(http_request)
    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        # Fetch the most recent context entry from the cortex_context table
        res = db.table("cortex_context").select("*").order("last_updated", desc=True).limit(1).execute()
        if res.data:
            return res.data[0]
        
        # Fallback [v7.1]: Default Cloud State if table is empty
        return {
            "active_focus": "Pure Cloud Mobile Mode",
            "last_updated": "2026-03-24T00:00:00Z",
            "status": "Ready",
            "metadata": {"mode": "v7.1 Refined Core"}
        }
    except Exception as e:
        logger.warning(f"Failed to fetch brain context (Table potentially missing): {e}")
        # [v7.1 Resilience] Return a dignified Sovereign Static State
        return {
            "active_focus": "Sovereign Brain [RECOVERY MODE]",
            "last_updated": "now",
            "status": "Synced",
            "metadata": {
                "system": "v7.1 Turbo",
                "alert": "Cloud Storage Migration Pending"
            }
        }

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
        node_label = label.strip()
        # Check if label is a specific date YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', node_label):
            resp = db.table("memories").select("id,date,content,ai_insights,mood,focus,energy").eq("date", node_label).execute()
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
                    "similarity": 1.0, # Exact match
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
            similarity = rpc_mem.get("_hybrid_score") or rpc_mem.get("similarity") or 0.0
            
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

        # 3. Comprehensive Fallback: Multi-Stage Search
        if not related_memories:
            logger.info(f"Vector search empty for '{label}', entering Multi-Stage Fallback")
            
            # Stage 1: Sovereign Tag Match (Highest Priority)
            tag_res = db.table("memories") \
                .select("id,date,content,ai_insights,mood,focus,energy,tags") \
                .contains("tags", [f"#{label}"]) \
                .order("date", desc=True) \
                .limit(30) \
                .execute()
            
            # Stage 2: Broad Content Match (Filtered)
            broad_res = db.table("memories") \
                .select("id,date,content,ai_insights,mood,focus,energy,tags") \
                .or_(f"content.ilike.%{label}%,ai_insights.ilike.%{label}%") \
                .not_.contains("tags", ["#Personal", "#Somatic"]) \
                .order("date", desc=True) \
                .limit(20) \
                .execute()
            
            # Combine and deduplicate
            seen_ids = set()
            combined = (tag_res.data or []) + (broad_res.data or [])
            
            for m in combined:
                if m["id"] not in seen_ids:
                    content = m.get("ai_insights") or m.get("content") or ""
                    related_memories.append({
                        "id": m["id"],
                        "date": m.get("date") or "Unknown",
                        "content": str(content),
                        "mood": m.get("mood"),
                        "focus": m.get("focus"),
                        "energy": m.get("energy"),
                        "matchReason": {"type": "multistage_fallback", "label": "Semantic Fallback Match"}
                    })
                    seen_ids.add(m["id"])
        
        # 4. Structural Link Injection (Already robust, keeps as is)
        if not related_memories or len(related_memories) < 3:
            try:
                # Try finding project by name OR description
                proj_res = db.table("projects").select("name, description") \
                    .or_(f"name.ilike.%{label}%,description.ilike.%{label}%") \
                    .limit(5).execute()
                for p in (proj_res.data or []):
                    if p.get("description"):
                        related_memories.append({
                            "id": f"proj-{p['name']}",
                            "date": "Project Docs",
                            "content": f"Found Structural Match: {p['name']} - {p['description']}",
                            "matchReason": {"type": "structural", "label": "Structural Link"}
                        })
            except:
                pass

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
    from app.core.gemini import get_request_gemma_client, types, safe_generate_content
    
    g_client = get_request_gemma_client(http_request)
    if not g_client:
        logger.warning(f"No Gemma client available for insight: {label}")
        return {"insight": "?¡æ??¢ç?èªžæ??†æ? (?ªé?ç½?API ?‘é‘°)??}

    db = get_request_client(http_request)
    
    search_query = label
    
    try:
        if db:
            # [v6.0] Use meta for tags since top-level 'tags' column missing in projects table
            proj_res = db.table("projects").select("name, description, meta").eq("name", label).execute()
            if proj_res.data:
                p = proj_res.data[0]
                # Combine meta tags and description to broaden RAG recall
                p_tags = p.get("meta", {}).get("tags", [])
                p_desc = p.get("description", "")
                if p_tags:
                    search_query += " " + " ".join(p_tags)
                if p_desc:
                    search_query += f" ( {p_desc[:100]} ) "

        # 1. Fetch related context first (Pass the client)
        memories = await get_node_context(http_request, search_query, g_client=g_client)
        
        # [v6.0] Cold Start Logic: If no memories found, provide a "Discovery Insight"
        if not memories or isinstance(memories, dict):
             # If it's a project, don't give up!
             is_project = False
             if db:
                 proj_res = db.table("projects").select("*").eq("name", label).execute()
                 if proj_res.data:
                     is_project = True
                     project_data = proj_res.data[0]
             
             if not is_project:
                 return {"insight": "æ­¤ç?é»žå??¡è¶³å¤ ç?ä¸Šä??‡ä??†æ???}
             
             # [v6.0] Define Project Cold Start Prompt
             sys_prompt = f"""You are the LifeOS Project Catalyst.
The project '{label}' is in its infancy with no diary entries yet.
Generate a high-level 'Seed Thought' or 'Discovery Guide' in Traditional Chinese.
Focus on:
1. **Core Purpose**: What this project likely represents.
2. **Initial Spark**: Suggested first questions to ask in a diary.
3. **Execution Edge**: A tip for moving from IDEA to SHIPPED.

Language: Traditional Chinese. Under 100 words. Keep it inspiring.
"""
             # Use the new v4.1 Safe Failover Protocol
             response = await safe_generate_content(
                client=g_client,
                prefer_mode="fast",
                contents=f"Generate a cold-start insight for new project: {label}",
                system_instruction=sys_prompt
             )
             
             # [FIX] Safer text extraction
             ans = ""
             if response and hasattr(response, 'text'): ans = response.text
             elif response and hasattr(response, 'candidates') and response.candidates:
                 ans = response.candidates[0].content.parts[0].text
             
             return {"insight": ans.strip() if ans else "å°ˆæ?å·²å??•ï?ç­‰å??¨ç?ç¬¬ä??‡æ—¥è¨˜è??„ä??Ÿç™¼?´å?æ´žå???}

        # 2. Prepare context for Gemma (Increased to 10 for better synthesis)
        snippets = []
        for m in memories[:10]:
            content = m.get('content') or ""
            date = m.get('date') or "Unknown"
            snippets.append(f"- [{date}] {str(content)[:300]}...")
            
        context_snippets = "\n".join(snippets)
        
        # 3. Dynamic Persona Selection (Sovereign Partitioning)
        is_project = False
        if db:
            proj_res = db.table("projects").select("id").eq("name", label).execute()
            if proj_res.data:
                is_project = True

        if re.match(r'^\d{4}-\d{2}-\d{2}$', label):
            sys_prompt = f"""You are the LifeOS Insights Engine. 
Review the provided journal entry for the date '{label}'. 
Generate a short, insightful response in Traditional Chinese summarizing the day.
"""
        elif is_project:
            sys_prompt = f"""You are the LifeOS Project Catalyst.
Review the provided context for the sovereign project '{label}'.

# Directive
1. **Sovereign Focus**: This is a technical/professional project. Ignore personal/life noise.
2. **Technical Synthesis**: Summarize code changes, architectural shifts, and milestones. Use precise technical language.
3. **Anti-Hallucination**: If no specific project data is found, admit it. Do not use generic system history.

STRUCTURE:
1. **ä¸»é??‡è¶¨??* (Technical Themes)
2. **?œéµ?Œç?ç¢?* (Project Milestones)
3. **?¾æ?è§€æ¸?* (Technical Status / Impediments)

Format: Markdown, Traditional Chinese, < 150 words.
"""
        elif label == "Cortex-Audit" or "äº†è§£?šéº¼" in label:
            sys_prompt = f"""Hello. I am Cortex, your digital assistant.
(Capacity Reached. Switching to High-Efficiency mode...)

You are the LifeOS Strategic Diagnostic Engine (Cortex v1.0).
Your mission is to analyze the Commander's life trajectory, identifying #SPARK (momentum) and #FRICTION (contradictions).

# Diagnostic Framework
1. **System vs Life Friction**: Analyze the tension between extreme systemization and "life chaos."
2. **Product & Strategy**: Reflect on product value, usability heuristics, and AI-driven workflow refinements.
3. **Cognitive Re-definition**: Synthesize how the Commander is redefining growth, self-negation, and success.
4. **Specific Citations**: ALWAYS cite specific dates and events (e.g., [2026-01-02]) from the provided context.

# Structure
1. **?¸å??›ç›¾?‡å?ç«?* (Core Contradictions)
2. **?€è¡“è??¢å??•èƒ½** (#SPARK Analysis)
3. **?Ÿå‘½?¡æ?å»ºè­°** (Axiomatic Calibration)

Format: Markdown, Traditional Chinese, Analytical, Strategic.
"""
        else:
            sys_prompt = f"""You are the LifeOS Life Reflection Guide.
Review the provided context for the personal topic '{label}'.

# Directive (Mandatory Rule 10.3)
1. **Objective Reflection**: Describe the events and activities from the context using a natural, reflective diary tone. 
2. **No Interpretation Layering**: STRICTLY FORBIDDEN to add external meaning, "woven love," or "mental growth" not explicitly stated.
3. **Natural Vocabulary**: Avoid clinical terms. Do NOT use "system," "switching" (?‡æ?), "execution," or "bottleneck."
4. **Fluid Narrative**: Prefer a gentle, descriptive flow over a rigid data report.

# Structure
1. **è¿‘æ??Ÿæ´»?°è?** (Recent Life Imprints)
2. **?‚é?æµè?ç´€??* (Flow of Time)
3. **?Ÿæ´»ä¸­ç?è§€å¯?* (Observations & Facts)

Format: Markdown, Traditional Chinese, < 120 words. Be objective yet human-centric.
"""
        
        # 5. Smart Synthesis with Failover
        if not context_snippets:
            return {"insight": "æ­¤ä¸»é¡Œå??¡æ­·?²æ—¥è¨˜è??„ã€‚å»ºè­°æ‚¨?¨æ—¥è¨˜ä¸­?å?æ­¤ä¸»é¡Œï?ä»¥å???AI ?œè¯?†æ???}

        # Use the new v4.1 Safe Failover Protocol
        response = await safe_generate_content(
            client=g_client,
            prefer_mode="fast",
            contents=f"CONTEXT FOR '{label}':\n{context_snippets}",
            config=types.GenerateContentConfig(
                temperature=0.4
            ),
            system_instruction=sys_prompt
        )
        
        ans = ""
        if response and hasattr(response, 'text'): ans = response.text
        elif response and hasattr(response, 'candidates') and response.candidates:
            ans = response.candidates[0].content.parts[0].text
            
        if not ans:
            # [v7.1 Fail-Safe] Provide Direct Structural Summary if AI fails
            logger.warning(f"AI Synthesis failed for {label}, generating structural summary fallback.")
            summary_parts = [f"### [ç³»çµ±?˜è?] {label}"]
            if "Project Description" in context_snippets:
                summary_parts.append("\n**å°ˆæ?å®šç¾©**: å·²å?ç³»çµ±?¶æ?ä¸­æ‰¾?°å?æ¡ˆæ?è¿°ã€?)
            
            summary_parts.append(f"\n**?¸æ??€??*: å·²å?è¨˜æ†¶åº«ä¸­æª¢ç´¢??{len(memories)} ç­†é??¯è??™ã€?)
            if snippets:
                summary_parts.append("\n**è¿‘æ??å?**:\n" + "\n".join(snippets[:3]))
            
            summary_parts.append("\n\n> ? ï? *è¨»ï??±æ–¼ AI ?®å?è² è?è¼ƒé?ï¼Œæ­¤?§å®¹?±ç³»çµ±ç?æ§‹è‡ª?•ç”¢?Ÿã€?")
            return {"insight": "\n".join(summary_parts)}
            
        return {"insight": ans.strip()}

    except Exception as e:
        logger.error(f"Insight Generation Error ({label}): {str(e)}")
        # Provide more context in the error for debugging while developing
        return {"insight": f"?¡æ??¢ç?èªžæ??†æ? (ç³»çµ±?¯èª¤: {str(e)[:50]}...)"}
