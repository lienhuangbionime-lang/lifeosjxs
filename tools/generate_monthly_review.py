"""
Monthly Review Generator
Reads all memories for a given month, synthesizes them with Gemini, and saves the review.

Usage:
  python tools/generate_monthly_review.py <YEAR> <MONTH>
  Example: python tools/generate_monthly_review.py 2026 1
"""

import sys
import os
import argparse
import asyncio
from datetime import datetime, timedelta
import calendar
from dotenv import load_dotenv

# Fix Windows Unicode output issues
sys.stdout.reconfigure(encoding='utf-8')

# Add backend-cortex path to sys.path so app imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend-cortex")))

# Load .env explicitly from backend-cortex
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend-cortex", ".env")))

try:
    from app.core.database import supabase
    from google import genai
    from google.genai import types
    from app.core.config import settings
except ImportError as e:
    print(f"[ERROR] Missing dependencies: {e}")
    sys.exit(1)


REVIEW_PROMPT = """
You are the Cortex Monthly Review Agent.
Below are the daily summaries from the user for the month of {month_name} {year}.

Your task is to synthesize these into a high-level Monthly Review.
Focus on patterns, major achievements, recurring challenges, and emotional shifts.

Structure your response in Markdown:

# Monthly Review: {month_name} {year}

## 🏆 Key Achievements
- ...

## 🧗 Challenges & Roadblocks
- ...

## 💡 Insights & Lessons Learned
- ...

## 🔋 Energy & Mood Trends
- ...

## 🎯 Focus for Next Month
- ...

---
Daily Summaries:
{daily_summaries}
"""

async def generate_review(year: int, month: int):
    print(f"🔄 Generating Monthly Review for {year}-{month:02d}...")

    # 1. Fetch memories
    start_date = f"{year}-{month:02d}-01"
    _, last_day = calendar.monthrange(year, month)
    end_date = f"{year}-{month:02d}-{last_day}"

    if not supabase:
        print("[ERROR] Supabase client not initialized.")
        return

    print(f"  - Fetching memories from {start_date} to {end_date}...")
    response = supabase.table("memories") \
        .select("date, content, mood, energy") \
        .gte("date", start_date) \
        .lte("date", end_date) \
        .order("date") \
        .execute()

    memories = response.data
    if not memories:
        print("[WARN] No memories found for this month.")
        return

    print(f"  - Found {len(memories)} memories.")

    # 2. Prepare context for AI
    daily_summaries = []
    for m in memories:
        date_str = m.get('date')
        content = m.get('content', 'No content.')
        # Limit content per day to avoid prompt explosion
        preview = content[:500] + "..." if len(content) > 500 else content
        mood = m.get('mood', 'N/A')
        energy = m.get('energy', 'N/A')
        daily_summaries.append(f"### {date_str} (Mood: {mood}, Energy: {energy})\n{preview}")
    
    context_text = "\n\n".join(daily_summaries)
    month_name = calendar.month_name[month]
    
    full_prompt = REVIEW_PROMPT.format(
        year=year,
        month_name=month_name,
        daily_summaries=context_text
    )

    # 3. Generate with Gemini
    print("  - Synthesizing with Gemini...")
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
         print("[ERROR] GEMINI_API_KEY not set.")
         return

    client = genai.Client(api_key=api_key)
    
    # [HARD TRUTH ALIGNMENT] Use verified model names from genai v1
    # [v3.5 Phase 11] Force proven high-context models for massive memory crunching
    models_to_try = [
        "gemini-pro-latest",         # Primary choice for 1M+ context synthesis
        "gemini-flash-latest",       # Highly stable fallback
        "gemini-flash-lite-latest"
    ]
    
    # Remove duplicates while preserving order
    models_to_try = list(dict.fromkeys(models_to_try))

    review_content = None
    for model_name in models_to_try:
        try:
            print(f"  - Trying model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            review_content = response.text
            print(f"  [OK] Successfully generated with {model_name}")
            break # Exit loop if successful
        except Exception as e2:
            print(f"  [WARN] Failed with {model_name}: {e2}")
            continue
            
    if not review_content:
        print("[ERROR] All models failed to generate review.")
        return

    # 4. Save to Supabase
    print("  - Saving to Database...")
    payload = {
        "year": year,
        "month": month,
        "summary": review_content,
        "created_at": datetime.now().isoformat()
    }
    
    try:
        # Note: Ensure MonthlyReview table has unique(year, month)
        supabase.table("MonthlyReview").upsert(payload, on_conflict="year,month").execute()
        print("  [OK] Saved to Supabase 'MonthlyReview' table.")
    except Exception as e:
        print(f"  [ERROR] Database save failed (Check if table exists): {e}")

    # 5. Save local Markdown (Backup)
    output_dir = "data/reviews"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{year}-{month:02d}_Review.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(review_content)
    
    print(f"  [OK] Saved local file: {filename}")
    print("\n✅ Monthly Review Generation Complete!")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tools/generate_monthly_review.py <YEAR> <MONTH>")
        sys.exit(1)
    
    y = int(sys.argv[1])
    m = int(sys.argv[2])
    
    asyncio.run(generate_review(y, m))
