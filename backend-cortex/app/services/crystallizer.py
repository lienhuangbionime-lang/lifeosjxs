
import json
import logging
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.core.gemini import gemini_client, get_model
from google.genai import types

logger = logging.getLogger("cortex.services.crystallizer")

class Crystallizer:
    """
    Extracts structural knowledge (Entities and Relationships) from raw text.
    Populates the 'nodes' and 'edges' tables to build the Neural Graph.
    """
    
    SYSTEM_PROMPT = """You are the Knowledge Extraction Engine for LifeOS. 
Review the provided diary entry or memory and extract key structural information.

1. **Nodes**: Identify specific entities mentioned.
   - Types: person, project, concept, tool, tag.
   - Label: Use a concise name (e.g., "Supabase", "Lien").
   
2. **Edges**: Identify relationships between the entry's Date and the Nodes, or between Nodes themselves.
   - Relation: Concise verb (e.g., "worked_on", "met", "used", "part_of").
   - Weight: 1-5 (1=mention, 5=primary focus).

Output ONLY a JSON object:
{
  "nodes": [{"label": "Name", "type": "concept"}],
  "edges": [{"source": "SourceLabel", "target": "TargetLabel", "relation": "verb", "weight": 3}]
}"""

    async def crystallize_memory(self, memory_id: str, content: str, date: str):
        """
        Process a single memory entry.
        Source for edges linked to the memory will be the date_id (YYYY-MM-DD).
        """
        if not gemini_client:
            logger.error("Gemini client not initialized")
            return

        try:
            # 1. Prompt Gemini via Safe Failover
            from app.core.gemini import safe_generate_content
            response = await safe_generate_content(
                client=gemini_client,
                prefer_mode="fast",
                contents=f"ENTRY DATE: {date}\nCONTENT: {content}",
                config=types.GenerateContentConfig(
                    system_instruction=self.SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            
            data = json.loads(response.text.strip())
            
            # 2. Map of Label -> UUID
            label_to_id = {}
            
            # 3. Handle Nodes & the Date node
            nodes = data.get("nodes", [])
            # Always ensure the date itself is a node if mentioned in edges
            if date not in [n.get("label") for n in nodes]:
                nodes.append({"label": date, "type": "concept"})

            for node_data in nodes:
                node_id = self._upsert_node(node_data)
                if node_id:
                    label_to_id[node_data["label"]] = node_id
                
            # 4. Insert Edges with UUID mapping
            for edge_data in data.get("edges", []):
                source_label = edge_data.get("source")
                target_label = edge_data.get("target")
                
                source_id = label_to_id.get(source_label)
                target_id = label_to_id.get(target_label)
                
                if source_id and target_id:
                    self._insert_edge(source_id, target_id, edge_data.get("relation"), edge_data.get("weight", 1))
                else:
                    logger.warning(f"Skipping edge: Could not resolve IDs for {source_label} -> {target_label}")
                
            logger.info(f"Crystallized memory {memory_id}: {len(nodes)} nodes, {len(data.get('edges', []))} edges.")
            
        except Exception as e:
            logger.error(f"Crystallization failed for {memory_id}: {e}")

    def _upsert_node(self, node: Dict[str, str]) -> Optional[str]:
        """Ensure node exists in the 'nodes' table and return its UUID."""
        label = node.get("label")
        if not label: return None
        
        try:
            logger.info(f"Adding node: {label}")
            # Upsert by label (unique constraint)
            # Use PostgREST upsert with 'on_conflict'
            res = supabase.table("nodes").upsert({
                "label": label,
                "type": node.get("type", "concept")
            }, on_conflict="label").execute()
            
            if res.data:
                logger.info(f"Node upserted: {label} -> {res.data[0]['id']}")
                return res.data[0]["id"]
            
            logger.warning(f"Upsert returned no data for {label}")
            return None
        except Exception as e:
            logger.error(f"Node upsert failed ({label}): {e}")
            return None

    def _insert_edge(self, source_id: str, target_id: str, relation: str, weight: float):
        """Insert relationship into the 'edges' table using UUIDs."""
        try:
            logger.info(f"Adding edge: {source_id} -> {target_id} ({relation})")
            res = supabase.table("edges").upsert({
                "source_id": source_id,
                "target_id": target_id,
                "relation": relation or "related",
                "weight": float(weight)
            }, on_conflict="source_id,target_id,relation").execute()
            logger.info(f"Edge upserted: {len(res.data or [])} record(s)")
        except Exception as e:
            logger.error(f"Edge insert failed ({source_id}->{target_id}): {e}")

crystallizer = Crystallizer()
