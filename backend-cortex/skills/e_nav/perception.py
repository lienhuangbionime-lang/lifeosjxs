import httpx
from bs4 import BeautifulSoup
from typing import List
from skills.e_nav.schema import NomadEntity
import logging

logger = logging.getLogger("cortex.enav.perception")

async def fetch_external_map(url: str) -> List[NomadEntity]:
    """
    Scrapes external food maps (e.g., Siktung Tainan).
    Converts 'Beef Soup', 'Old House Cafe' labels into system vibe_tags.
    
    Architecture Rules:
    - Mark as source="external_curation"
    - Normalize cuisine tags.
    """
    logger.info(f"Scraping external map: {url}")
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            nomads = []
            
            # Pattern matching for siktungtainan.com and similar WordPress-style food blogs
            articles = soup.find_all('article')
            
            for art in articles:
                try:
                    title_tag = art.find(['h1', 'h2', 'h3'])
                    if not title_tag: continue
                    name = title_tag.get_text().strip()
                    
                    # Extract labels / categories
                    raw_labels = [tag.get_text().strip() for tag in art.find_all('a', rel='tag')]
                    
                    vibe_tags = ["私廚特選"]
                    cuisine = "未知"
                    
                    # Heuristic tagging logic
                    lower_name = name.lower()
                    if any(x in lower_name or any(x in l.lower() for l in raw_labels) for x in ["牛肉湯", "beef soup"]):
                        vibe_tags.append("台南牛肉湯地圖")
                        cuisine = "台式牛肉湯"
                    elif any(x in lower_name for x in ["老屋", "咖啡", "cafe"]):
                        vibe_tags.append("老屋巡禮")
                        cuisine = "咖啡廳"
                    elif "排隊" in str(art) or "名店" in str(art):
                        vibe_tags.append("排隊名店")
                    
                    nomad = NomadEntity(
                        name=name,
                        cuisine=cuisine,
                        source="external_curation",
                        vibe_tags=vibe_tags,
                        is_never_visited=True,
                        trust_score=90  # Default trust for curated lists
                    )
                    nomads.append(nomad)
                except Exception as e:
                    logger.debug(f"Skipping article due to parse error: {e}")
                    continue
            
            return nomads
        except Exception as e:
            logger.error(f"Scraping {url} failed: {e}")
            return []

async def ingest_nomads_task():
    """
    Main ingestion entry point for CLI and Scheduler.
    """
    sources = [
        "https://siktungtainan.com/",  # 台南食通
        "https://taiwanfoodmap.com/"   # 全台美食地圖 (Placeholder)
    ]
    
    all_nomads = []
    for source_url in sources:
        results = await fetch_external_map(source_url)
        all_nomads.extend(results)
        
    logger.info(f"Ingestion complete: {len(all_nomads)} entities extracted.")
    return all_nomads
