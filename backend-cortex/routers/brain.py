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

@router.delete("/node/{label}")
async def delete_brain_node(label: str):
    """
    Delete a node from the Knowledge Graph by its label.
    If it's a log node, also delete the corresponding memory entry.
    """
    try:
        if not memory_service.client:
            raise HTTPException(status_code=503, detail="Database connection unavailable")

        # 1. Check if node exists and get metadata
        node_res = memory_service.client.table("nodes").select("*").eq("label", label).execute()
        if not node_res.data:
            raise HTTPException(status_code=404, detail=f"Node '{label}' not found")
        
        node = node_res.data[0]
        metadata = node.get("metadata", {})

        # 2. If it's a log, try to delete the actual memory record
        if metadata.get("is_log"):
            # Try memory_id first, then fallback to date
            memory_id = metadata.get("memory_id")
            if memory_id:
                print(f"Deleting memory by ID: {memory_id}")
                memory_service.client.table("memories").delete().eq("id", memory_id).execute()
            else:
                # Fallback: Delete based on date (label)
                print(f"Deleting memory by date: {label}")
                memory_service.client.table("memories").delete().eq("date", label).execute()

        # 3. Delete the node (Associated edges will be deleted via CASCADE)
        res = memory_service.client.table("nodes").delete().eq("label", label).execute()
        
        return {"status": "success", "message": f"Node '{label}' and its records deleted."}
    except Exception as e:
        print(f"Node deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
