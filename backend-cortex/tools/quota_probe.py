"""
Quota-Aware Dynamic Model Probe (v5.4)
Replaces all hardcoded model IDs in gemini.py with live-discovered, sandbox-verified models.

Strategy:
1. Call client.models.list() to get ALL available models (same as test.py)
2. Rank by version score (heuristic: newer = better)
3. Sandbox-test top candidates with a minimal generation call
4. Save the FIRST models that respond successfully as fast/smart in model_registry.json
5. Zero hardcoded model names — entirely dynamic

Run any time quota changes: python tools/quota_probe.py
"""
import asyncio
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

REGISTRY_PATH = Path(__file__).parent.parent / "data" / "model_registry.json"


def rank_model(name: str) -> float:
    """
    Heuristic ranking — higher = prefer for production.
    Flash = fast tier, Pro = smart tier.
    Newer version numbers rank higher.
    'lite' or 'nano' ranks slightly lower (lower cost but also lower capability).
    'preview'/'exp' ranks slightly higher (bleeding edge).
    'latest' alias is mid-tier.
    """
    score = 0.0
    # Version bumps
    for ver, pts in [("3.1", 100), ("3.0", 90), ("3", 80), ("2.5", 60), ("2.0", 40), ("1.5", 20)]:
        if ver in name:
            score += pts
            break
    
    # [v5.6] Alias support
    if "latest" in name:
        if "pro" in name: score += 85 # Pro-latest is usually 1.5 or 1.0 Pro
        elif "flash" in name: score += 75 # Flash-latest is usually 1.5 Flash
    # Modifiers
    if "lite" in name or "nano" in name:
        score -= 10
    if "preview" in name or "exp" in name:
        score += 5
    if "latest" in name:
        score += 2
    return score


async def sandbox_test(model_id: str) -> bool:
    """Minimal generation test — returns True only if model replies with text."""
    try:
        response = await client.aio.models.generate_content(
            model=model_id,
            contents="Reply only: OK",
            config=types.GenerateContentConfig(max_output_tokens=5)
        )
        return bool(response and response.text and response.text.strip())
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            print(f"  [QUOTA] {model_id}: quota_exhausted")
        elif "404" in err or "not found" in err.lower():
            print(f"  [NOT_FOUND] {model_id}")
        else:
            print(f"  [ERROR] {model_id}: {err[:80]}")
        return False


async def main():
    print("=" * 60)
    print("LifeOS Quota-Aware Model Discovery (v5.4)")
    print("=" * 60)

    # 1. List all models from API (same as test.py pattern)
    all_flash = []
    all_pro = []
    print("\n[STEP 1] Listing all available models from API...")
    for m in client.models.list():
        name = m.name
        if "flash" in name.lower():
            all_flash.append(name)
        elif "pro" in name.lower() and "gemma" not in name.lower():
            all_pro.append(name)

    # 2. Rank by version heuristic
    all_flash.sort(key=rank_model, reverse=True)
    all_pro.sort(key=rank_model, reverse=True)
    print(f"  Found {len(all_flash)} flash models, {len(all_pro)} pro models")
    print(f"  Flash ranked: {all_flash[:5]}")
    print(f"  Pro ranked: {all_pro[:3]}")

    # 3. Sandbox test (top candidates first, stop when we find one that works)
    print("\n[STEP 2] Sandbox testing top candidates...")
    available_fast = []
    quota_exhausted_fast = []
    for model_id in all_flash[:6]:  # Test top 6 flash candidates
        if await sandbox_test(model_id):
            print(f"  [OK] {model_id}: available")
            available_fast.append(model_id)
        else:
            quota_exhausted_fast.append(model_id)

    available_smart = []
    quota_exhausted_smart = []
    for model_id in all_pro[:4]:  # Test top 4 pro candidates
        if await sandbox_test(model_id):
            print(f"  [OK] {model_id}: available")
            available_smart.append(model_id)
        else:
            quota_exhausted_smart.append(model_id)

    # 4. Build and persist registry
    registry = {
        "verified_models": {
            "fast": available_fast,
            "smart": available_smart
        },
        "quota_exhausted": {
            "fast": quota_exhausted_fast,
            "smart": quota_exhausted_smart
        },
        "pending_models": {"fast": [], "smart": []},
        "last_discovery": datetime.now().isoformat(),
    }

    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    # 5. Report
    print("\n" + "=" * 60)
    print(f"REGISTRY SAVED: {REGISTRY_PATH}")
    print(f"  Fast (available): {available_fast}")
    print(f"  Smart (available): {available_smart}")
    print(f"  Fast (quota exhausted): {quota_exhausted_fast}")
    print(f"  Smart (quota exhausted): {quota_exhausted_smart}")

    if not available_fast:
        print("\n  [WARN] No fast models available. All quota may be exhausted.")
        print("  Suggestion: Wait for quota reset or check AI Studio rate limits.")
    if not available_smart:
        print("\n  [INFO] No smart/pro models available right now.")

    print("=" * 60)


asyncio.run(main())
