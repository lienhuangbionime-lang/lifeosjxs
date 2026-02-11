from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Union, Optional
import re
import sys
from pathlib import Path

# Add backend-cortex to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.memory_service import memory_service

router = APIRouter(prefix="/api/v1/brain", tags=["Brain"])

# --- Models ---
class GraphNode(BaseModel):
    id: str
    group: Union[int, str]
    val: float
    raw: Optional[Dict[str, Any]] = None

class GraphLink(BaseModel):
    source: str
    target: str
    value: float

class GraphData(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    answer: str
    context: List[Any] = []

# --- Endpoints ---

@router.get("/graph", response_model=GraphData)
def get_brain_graph(limit: int = 1000):
    """
    Get Knowledge Graph directly from Supabase nodes and edges tables.
    This ensures the graph represents the actual structured data in the DB.
    """
    try:
        if not memory_service.client:
             return GraphData(nodes=[], links=[])

        # 1. Fetch Nodes
        nodes_res = memory_service.client.table("nodes").select("*").limit(limit).execute()
        db_nodes = nodes_res.data if nodes_res.data else []

        # 2. Fetch Edges
        edges_res = memory_service.client.table("edges").select("*").limit(limit * 2).execute()
        db_edges = edges_res.data if edges_res.data else []

        # 3. Map to GraphNode
        formatted_nodes = []
        for n in db_nodes:
            # Determine group based on type
            group_map = {"log": 1, "tag": "tag", "person": "person", "concept": "concept"}
            node_metadata = n.get("metadata", {})
            node_type = n.get("type", "concept")
            
            # If metadata has is_log, force it to group 1 (Log)
            if node_metadata.get("is_log"):
                group = 1
                val = 6
            else:
                group = group_map.get(node_type, "concept")
                # Val (size) based on importance
                if node_type == "person":
                    val = 5
                elif node_type == "concept":
                    val = 4
                else:
                    val = 3
            
            formatted_nodes.append(GraphNode(
                id=n["label"], # UI expects label as ID for matching links
                group=group,
                val=val,
                raw=n.get("metadata", {})
            ))

        # 4. Map to GraphLink
        formatted_links = []
        # We need a label map to convert source_id (UUID) to label (String ID) for D3
        id_to_label = {n["id"]: n["label"] for n in db_nodes}
        
        for e in db_edges:
            source_label = id_to_label.get(e["source_id"])
            target_label = id_to_label.get(e["target_id"])
            
            if source_label and target_label:
                formatted_links.append(GraphLink(
                    source=source_label,
                    target=target_label,
                    value=e.get("weight", 1.0)
                ))

        return GraphData(nodes=formatted_nodes, links=formatted_links)

    except Exception as e:
        print(f"Graph retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask", response_model=AskResponse)
async def ask_brain(request: AskRequest):
    """
    RAG Chat Endpoint (Gemini)
    """
    try:
        answer = await memory_service.ask_brain(request.query)
        return AskResponse(answer=answer, context=[])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
