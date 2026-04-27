import os
from typing import List, Dict, Any
from app.services.memory_service import memory_service
from app.core.gemini import get_gemma_client, safe_generate_content

class RadarAgent:
    def __init__(self):
        self.client = get_gemma_client()

    async def scan_for_signals(self) -> List[Dict[str, Any]]:
        """
        Scan the Knowledge Graph for nodes tagged as #SPARK or #FRICTION 
        that aren't yet on the Radar.
        """
        if not memory_service.client:
            return []

        # 1. Fetch potential nodes (concepts/tags)
        # We look for nodes that are related to #SPARK or #FRICTION tags
        try:
            # Get the IDs of #SPARK and #FRICTION tags
            tags_res = memory_service.client.table("nodes").select("id").in_("label", ["SPARK", "FRICTION"]).execute()
            tag_ids = [t["id"] for t in tags_res.data] if tags_res.data else []
            
            if not tag_ids:
                return []

            # Find neighbors of these tags
            edges_res = memory_service.client.table("edges").select("target_id").in_("source_id", tag_ids).execute()
            neighbor_ids = [e["target_id"] for e in edges_res.data] if edges_res.data else []
            
            if not neighbor_ids:
                return []

            # Fetch the neighbor nodes that don't have radar_status
            nodes_res = memory_service.client.table("nodes").select("*").in_("id", neighbor_ids).execute()
            potential_signals = []
            for n in nodes_res.data:
                meta = n.get("metadata", {})
                if not meta or "radar_status" not in meta:
                    potential_signals.append(n)
            
            return potential_signals
        except Exception as e:
            print(f"[RadarAgent] Scan error: {e}")
            return []

    async def evaluate_signal(self, node_label: str, content_context: str) -> Dict[str, Any]:
        """
        Use AI to evaluate if a signal is worth "Watching" on the Radar.
        """
        prompt = f"""
        Analyze this potential "Sovereign Signal" for the LifeOS Radar.
        Signal Label: {node_label}
        Context: {content_context}
        
        Evaluate the "Sovereign Value" (intentionality, leverage, aesthetic impact) and 
        recommend if it should be tracked on the Radar.
        
        Output JSON:
        {{
            "should_track": bool,
            "priority": int (1-10),
            "reasoning": "string",
            "initial_status": "watching"
        }}
        """
        
        try:
            response = await safe_generate_content(
                client=self.client,
                prefer_mode="fast",
                contents=prompt
            )
            import json
            import re
            # Extract JSON
            match = re.search(r"\{.*\}", response.text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {"should_track": False}
        except Exception as e:
            print(f"[RadarAgent] Evaluation error: {e}")
            return {"should_track": False}
