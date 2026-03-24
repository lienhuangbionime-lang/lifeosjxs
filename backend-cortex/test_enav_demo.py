import asyncio
import sys
import os

# Inject path for cortex imports
sys.path.append(os.getcwd())

from skills.e_nav.perception import ingest_nomads_task
import json

async def test_enav_perception():
    print("🚀 Starting E-Nav Perception Engine...")
    print("📡 Scraping 'Siktung Tainan' (台南食通) for local delicacies...")
    
    try:
        nomads = await ingest_nomads_task()
        
        print(f"\n✅ Total Nomads Found: {len(nomads)}")
        print("-" * 50)
        
        for i, nomad in enumerate(nomads[:5]):
            print(f"[{i+1}] {nomad.name}")
            print(f"    Cuisine: {nomad.cuisine}")
            print(f"    Vibe Tags: {', '.join(nomad.vibe_tags)}")
            print(f"    Trust Score: {nomad.trust_score}")
            print("-" * 30)
            
        if len(nomads) > 5:
            print(f"... and {len(nomads) - 5} more.")
            
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")

if __name__ == "__main__":
    asyncio.run(test_enav_perception())
