from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.memory_service import memory_service
from app.agents.radar_agent import RadarAgent

router = APIRouter(prefix="/api/v1/radar", tags=["Radar"])
agent = RadarAgent()

class PromoteRequest(BaseModel):
    label: str
    target_status: str # watching, validating, building, shipped
    meta_updates: Optional[Dict[str, Any]] = None

@router.get("/signals")
async def get_radar_signals():
    """Get all nodes currently on the Radar, grouped by status."""
    if not memory_service.client:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        # Fetch all nodes that have radar_status in metadata
        # Supabase jsonb filtering: metadata->>radar_status IS NOT NULL
        # But for now, we'll fetch concepts and tags and filter in memory for simplicity/reliability
        res = memory_service.client.table("nodes").select("*").execute()
        nodes = res.data if res.data else []
        
        radar_groups = {
            "watching": [],
            "validating": [],
            "building": [],
            "shipped": []
        }
        
        for n in nodes:
            meta = n.get("metadata")
            if meta and "radar_status" in meta:
                status = meta["radar_status"]
                if status in radar_groups:
                    radar_groups[status].append(n)
        
        return radar_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/promote")
async def promote_signal(req: PromoteRequest):
    """Update the radar status of a node."""
    if not memory_service.client:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        # 1. Get current node
        res = memory_service.client.table("nodes").select("*").eq("label", req.label).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Node not found")
        
        node = res.data[0]
        meta = node.get("metadata", {})
        
        # 2. Update metadata
        meta["radar_status"] = req.target_status
        meta["last_status_change"] = datetime.now().isoformat()
        if req.meta_updates:
            meta.update(req.meta_updates)
        
        # 3. Save back to Supabase
        update_res = memory_service.client.table("nodes").update({"metadata": meta}).eq("id", node["id"]).execute()
        
        return {"status": "success", "node": update_res.data[0] if update_res.data else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan")
async def scan_new_signals():
    """Scan the graph for new potential signals to add to the Radar."""
    signals = await agent.scan_for_signals()
    return {"potential_signals": signals}
