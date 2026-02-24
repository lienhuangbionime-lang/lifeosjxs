#!/usr/bin/env python3
"""
tools/batch_embed.py — 歷史記憶向量化工具
目的: 掃描所有沒有 embedding 的 memories，補上 gemini-embedding-001 向量
執行: python tools/batch_embed.py [--limit N] [--dry-run]

注意:
  - gemini-embedding-001 輸出 3072 維
  - VECTOR(3072) 必須在 memories 表存在
  - 免費配額: ~1500 embed/day (需要多次執行)
"""
import os, sys, argparse, asyncio, time
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "backend-cortex"))

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, "backend-cortex", ".env"))

from app.core.database import supabase
from app.services.embedder import generate_embedding


def print_section(title):
    print(f"\n{'='*50}\n  {title}\n{'='*50}")


async def run(limit: int, dry_run: bool, delay: float):
    print_section(f"Batch Embed — limit={limit}, dry_run={dry_run}")

    # 1. Fetch memories without embedding
    res = supabase.table("memories") \
        .select("id,date,content,ai_insights") \
        .is_("embedding", "null") \
        .order("date", desc=False) \
        .limit(limit) \
        .execute()

    memories = res.data or []
    print(f"  Found {len(memories)} memories without embedding")

    if not memories:
        print("  [OK] All memories already have embeddings.")
        return

    success, fail = 0, 0

    for i, mem in enumerate(memories):
        date = mem.get("date", "?")
        content = mem.get("ai_insights") or mem.get("content") or ""
        if not content.strip():
            print(f"  [{i+1}/{len(memories)}] SKIP {date} — empty content")
            continue

        print(f"  [{i+1}/{len(memories)}] Processing {date}...", end=" ", flush=True)

        if dry_run:
            print("DRY_RUN (skipped)")
            continue

        embedding = await generate_embedding(content, task_type="retrieval_document")

        if embedding:
            try:
                supabase.table("memories") \
                    .update({"embedding": embedding}) \
                    .eq("id", mem["id"]) \
                    .execute()
                print(f"[OK] dim={len(embedding)}")
                success += 1
            except Exception as e:
                print(f"[ERROR] DB update failed: {e}")
                fail += 1
        else:
            print("[ERROR] Embedding generation failed")
            fail += 1

        # Rate limiting
        if i < len(memories) - 1:
            time.sleep(delay)

    print_section("Summary")
    print(f"  Success: {success}  |  Failed: {fail}  |  Total: {len(memories)}")
    if success < len(memories):
        print(f"  Run again to process remaining {len(memories) - success} memories.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50, help="Max memories to process per run")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between API calls (seconds)")
    args = parser.parse_args()

    asyncio.run(run(args.limit, args.dry_run, args.delay))
