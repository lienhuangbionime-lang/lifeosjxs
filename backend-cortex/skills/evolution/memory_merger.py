import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Sovereign Memory Merger v1.0
# Goal: Compare "Old Brain Files" with "New Memories" and suggest consolidations.

class MemoryMerger:
    def __init__(self):
        load_dotenv("backend-cortex/.env")
        self.supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        self.brain_dir = Path("sync_brain")

    async def merge_context(self, domain="BRAND_CORE"):
        print(f"MERGER: Starting Memory Merge for Domain: {domain}")
        
        # 1. Read the "Current Truth" (Old Data)
        truth_path = self.brain_dir / f"{domain}.md"
        old_truth = ""
        if truth_path.exists():
            with open(truth_path, "r", encoding="utf-8") as f:
                old_truth = f.read()

        # 2. Fetch "New Delta" (Last 5-10 memories related to domain)
        res = self.supabase.table("memories").select("*").ilike("content", f"%{domain}%").order("date", desc=True).limit(5).execute()
        new_memories = res.data or []
        
        if not new_memories:
            print(f"📭 No new updates found for {domain}. Skipping merge.")
            return None

        # 3. Use Gemini to "Resolve and Merge"
        from app.core.gemini import get_model, safe_generate_content, get_gemini_client
        client = get_gemini_client()
        
        new_text = "\n".join([m["content"] for m in new_memories])
        
        prompt = f"""
你是一個記憶整合大腦。請比對以下「舊有的核心定義」與「最新的實踐紀錄」，並生成一份整合後的版本。

【舊有的核心定義 ({domain})】:
{old_truth}

【最新的實踐紀錄】:
{new_text}

【要求】:
1. 保留核心精神，但根據最新的紀錄進行更新。
2. 如果新紀錄與舊定義有衝突，以「最新紀錄」為準（代表主權的演化）。
3. 輸出完整的 Markdown 內容。
"""

        try:
            response = await safe_generate_content(
                client=client,
                prefer_mode="smart",
                contents=prompt
            )
            merged_content = response.text
        except Exception as e:
            print(f"❌ Merge failed: {e}")
            return None

        # 4. Save to a temporary "Proposed" file for User Review
        merge_path = self.brain_dir / f"{domain}_PROPOSED_MERGE.md"
        with open(merge_path, "w", encoding="utf-8") as f:
            f.write(merged_content)
            
        print(f"DONE: Merged version saved to: {merge_path}. Waiting for approval.")
        return merge_path

if __name__ == "__main__":
    merger = MemoryMerger()
    asyncio.run(merger.merge_context("BRAND_CORE"))
