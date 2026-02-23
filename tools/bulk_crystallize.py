
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Load environment before importing app modules
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend-cortex', '.env')))

# Add backend-cortex to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend-cortex')))

from app.core.database import supabase
from app.services.crystallizer import crystallizer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bulk_crystallize")

async def run_bulk_crystallization(limit: int = 100):
    """
    Fetch historical memories and process them through the crystallizer.
    """
    logger.info(f"🚀 Starting bulk crystallization (limit={limit})...")
    
    try:
        # 1. Fetch memories
        response = supabase.table("memories").select("id, content, date").order("date", desc=True).limit(limit).execute()
        memories = response.data or []
        
        if not memories:
            logger.info("No memories found to process.")
            return
            
        logger.info(f"Found {len(memories)} memories. Processing...")
        
        # 2. Process each
        for i, mem in enumerate(memories):
            logger.info(f"[{i+1}/{len(memories)}] Processing {mem['date']} (ID: {mem['id']})...")
            await crystallizer.crystallize_memory(mem['id'], mem['content'], mem['date'])
            # rate limiting safety
            await asyncio.sleep(1) 
            
        logger.info("✅ Bulk crystallization complete.")
        
    except Exception as e:
        logger.error(f"Bulk processing failed: {e}")

if __name__ == "__main__":
    load_dotenv('backend-cortex/.env')
    
    # Get limit from args if provided
    limit = 20
    if len(sys.argv) > 1:
        try: limit = int(sys.argv[1])
        except: pass
        
    asyncio.run(run_bulk_crystallization(limit))
