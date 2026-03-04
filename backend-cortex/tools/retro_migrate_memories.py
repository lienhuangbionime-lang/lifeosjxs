import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables FIRST before importing backend modules
load_dotenv()

# Add backend directory to path so we can import app modules
curr_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(curr_dir, '..'))
sys.path.append(backend_dir)

from app.core.database import get_supabase_client
from app.core.gemini import get_model, gemini_client, safe_generate_content

# We import the exact same prompt from ingest.py so the migration uses the literal latest brain
from app.api.v1.ingest import LIFEOS_V7_PROMPT

async def migrate_old_memories():
    print("==================================================")
    print("  Starting Cortex Memory Retroactive Migration  ")
    print("==================================================")
    
    db = get_supabase_client()
    if not db:
        print("[ERROR] Supabase client not initialized. Check .env variables.")
        return

    # Check if we have the new columns
    try:
        # We try to select the new columns. If it fails, the user hasn't run the SQL yet.
        test_res = db.table("memories").select("id, is_private").limit(1).execute()
        print("[OK] Database schema confirmed. 'is_private' column exists.")
    except Exception as e:
        print(f"[ERROR] Database schema error: {e}")
        print("[WARN] Have you run the 010_add_v7_ingest_fields.sql script in Supabase yet?")
        return

    # 1. Fetch old memories that don't have the new JSON facts or were processed before this update
    # We look for memories where `facts` is null or empty, meaning they haven't been v7 processed.
    # Note: Not all might have `facts`, so we can just look for records where `is_private` is specifically null or where we decide to force a run.
    # For safety, let's fetch all memories that have an empty facts array and exist.
    print("[INFO] Fetching legacy memories...")
    
    # We will grab all memories. To be safe, we only process those with content.
    res = db.table("memories").select("id, date, content, ai_insights").execute()
    all_memories = res.data or []
    
    print(f"Found {len(all_memories)} total memories in the archive.")
    
    if not all_memories:
        print("No memories to migrate.")
        return
        
    client = gemini_client
    if not client:
        print("[ERROR] Gemini AI client not initialized (check GOOGLE_API_KEY). Cannot perform retro-processing.")
        return

    success_count = 0
    fail_count = 0
    
    for idx, mem in enumerate(all_memories):
        mem_id = mem['id']
        date_str = mem['date']
        
        # [v4.3 Fix] Use ai_insights as the primary source for retro-migration, 
        # since older versions might have mostly empty 'content' but rich 'ai_insights'
        raw_content = mem.get('content') or ""
        insights = mem.get('ai_insights') or ""
        
        content = insights if len(insights) > len(raw_content) else raw_content
        
        # Skip if empty content
        if not content or len(content.strip()) < 10:
            print(f"[{idx+1}/{len(all_memories)}] [SKIP] Skipping {date_str} (Empty or too short)")
            continue
            
        print(f"\n[{idx+1}/{len(all_memories)}] Re-processing memory from: {date_str}...")
        
        user_context = (
            f"[SYSTEM INSTRUCTION]\n"
            f"1. DATE: The target date for this log is {date_str}. You MUST replace [YYYY-MM-DD] in your output (Header and Graph Seeds) with {date_str}.\n"
            f"2. RETROACTIVE PROCESSING: You are re-evaluating an archiving log. Be extremely strict on Fact-Based Extraction.\n\n"
        )
        
        prompt = f"{LIFEOS_V7_PROMPT}\n\n{user_context}[USER LOG - {date_str}]:\n{content}"
        
        try:
            # Send to Gemini
            response = await safe_generate_content(
                client=client,
                prefer_mode="fast", # Use flash for batch processing
                contents=prompt
            )
            
            response_text = response.text.strip()
            
            # Extract JSON block
            import re
            import json
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if not json_match:
                # Try without markdown backticks
                json_match = re.search(r'\{(.*?)\}', response_text, re.DOTALL)
            
            ai_data = {}
            markdown_body = response_text
            
            if json_match:
                try:
                    # Parse JSON
                    json_str = json_match.group(1) if r'```' in json_match.group(0) else json_match.group(0)
                    ai_data = json.loads(json_str)
                    
                    # Remove the JSON completely from the markdown output so it doesn't pollute the UI
                    markdown_body = response_text.replace(json_match.group(0), "").strip()
                except Exception as je:
                    print(f"  [WARN] JSON parse warning for {date_str}: {je}")
            
            if not ai_data:
                print(f"  [ERROR] AI failed to return valid JSON for {date_str}. Skipping update.")
                fail_count += 1
                continue
                
            # Extract new fields
            meta = ai_data.get("meta", {})
            metrics = meta.get("metrics", {})
            
            is_private = ai_data.get("is_private", False)
            category = ai_data.get("category", "Life")
            facts = ai_data.get("facts", [])
            custom_metrics = ai_data.get("custom_metrics", {})
            
            # If the strict schema provided an explicit "markdown_body", use it. Otherwise use our stripped version.
            final_markdown = ai_data.get("markdown_body") or markdown_body
            
            print(f"  [INFO] Extracted: Category=[{category}], Private=[{is_private}], Facts count=[{len(facts)}]")
            
            # Update Database
            update_payload = {
                "is_private": is_private,
                "category": category,
                "facts": facts,
                "custom_metrics": custom_metrics,
                "ai_insights": final_markdown, # Clean markdown string
                "updated_at": "now()"
            }
            
            db.table("memories").update(update_payload).eq("id", mem_id).execute()
            print(f"  [OK] Successfully updated record {mem_id}")
            success_count += 1
            
            # Rate limiting safety for script (avoid hitting Gemini API limits)
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"  [ERROR] Error processing {date_str}: {e}")
            fail_count += 1

    print("\n==================================================")
    print(f"  Migration Complete! Successfully updated: {success_count}, Failed: {fail_count}")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(migrate_old_memories())
