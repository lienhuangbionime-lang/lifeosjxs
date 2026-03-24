import httpx
import os
from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class NomadPhoto(BaseModel):
    thumbnail: HttpUrl
    original: HttpUrl
    author: Optional[str] = None

async def fetch_nomad_photos(data_id: str, api_key: Optional[str] = None) -> List[NomadPhoto]:
    """
    Fetches real-time photos for a Google Maps entity using SerpApi.
    """
    final_api_key = api_key or os.getenv("SERPAPI_API_KEY")
    
    if not final_api_key:
        return []

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_maps_photos",
        "data_id": data_id,
        "api_key": final_api_key,
        "hl": "zh-tw"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            return []
        
        data = response.json()
        photos_data = data.get("photos", [])
        
        results: List[NomadPhoto] = []
        for p in photos_data[:5]:
            thumbnail = p.get("thumbnail")
            original = p.get("image")
            if thumbnail and original:
                results.append(NomadPhoto(
                    thumbnail=thumbnail,
                    original=original,
                    author=p.get("user", {}).get("name")
                ))
        return results
