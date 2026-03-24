import urllib.parse
from typing import Dict, Any

def generate_navigation_link(name: str, place_id: str = None) -> str:
    """
    Generates a Google Maps Deep Link for the user's 'Go Now' action.
    Complies with the v0 'Floating Action' requirement.
    """
    query = name
    base_url = "https://www.google.com/maps/search/?api=1"
    
    params = {"query": query}
    if place_id:
        params["query_place_id"] = place_id
        
    return f"{base_url}&{urllib.parse.urlencode(params)}"

def compare_logistics_prices(place_id: str) -> Dict[str, Any]:
    """
    Calculates UberEats / Foodpanda delivery fees and ETA.
    This serves the 'Logistics Pill' component in the v0 interface.
    """
    # In production, this would integrate with delivery platform APIs or scrapers
    return {
        "status": "active",
        "platforms": {
            "ubereats": {
                "available": True,
                "fee": 30.0,
                "eta": "18 min",
                "label": "快速送達"
            },
            "foodpanda": {
                "available": True,
                "fee": 25.0,
                "eta": "24 min",
                "label": "超值首選"
            }
        }
    }
