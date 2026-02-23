
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
import re
from app.core.database import supabase

router = APIRouter()
logger = logging.getLogger("cortex.brain")

@router.get("/graph")
async def get_brain_graph(limit: int = 500):
    """
    Generate the Neural Graph from memories.
    Replicates the logic of CoreEngine.parseGraphSeeds (Frontend) but on the backend.
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        # 1. Fetch recent memories
        response = supabase.table("memories").select("id,date,content,ai_insights,tags,mood,focus,energy").order("date", desc=True).limit(limit).execute()
        memories = response.data or []

        # 1.5 Fetch Structural Entities
        try:
            resp_proj = supabase.table("projects").select("id,name,status").in_("status", ["active", "on_hold"]).execute()
            projects = resp_proj.data or []
        except:
            projects = []

        try:
            resp_nodes = supabase.table("nodes").select("id,label,type").execute()
            db_nodes = resp_nodes.data or []
        except:
            db_nodes = []

        try:
            resp_edges = supabase.table("edges").select("source_id,target_id,relation,weight").execute()
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

            for i in range(len(processed_tags)):
                for j in range(i + 1, len(processed_tags)):
                    t1 = processed_tags[i]
                    t2 = processed_tags[j]
                    source, target = sorted([t1, t2])
                    add_link(source, target, 0.2)

        return {
            "nodes": list(nodes.values()),
            "links": list(links.values())
        }

    except Exception as e:
        logger.error(f"Graph Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
