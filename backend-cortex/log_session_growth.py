import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def log_error():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    # Log 1: Fallback logic mismatch
    supabase.table("cortex_growth_logs").insert({
        "decision_context": "Gemini Fallback Mechanism in chat.py",
        "options_provided": {"chain": ["gemini-flash-lite-latest", "gemini-1.5-flash-latest"]},
        "user_choice": "Auto-Correction required",
        "ai_prediction": "Fallback would succeed using global gemini_client",
        "prediction_match": False,
        "lessons_learned": "Critical: Use request-scoped 'req_gemini' client in FastAPI streams to avoid uninitialized variable crashes. Global clients are deprecated for multi-user/async contexts."
    }).execute()
    
    # Log 2: Quota Exhaustion handling
    supabase.table("cortex_growth_logs").insert({
        "decision_context": "Gemini Model Selection (v3.7.1)",
        "options_provided": {"models": ["1.5-flash", "flash-lite"]},
        "user_choice": "Extended fallback to 2.0 series",
        "ai_prediction": "1.5 models would have enough quota",
        "prediction_match": False,
        "lessons_learned": "Widespread free-tier 429 errors detected. Solution: Expand fallback chain to 2.0 flash/lite and implement ping-diagnostic scripts for faster recovery."
    }).execute()
    
    # Log 3: SDK Model Discovery (2.5 Series)
    supabase.table("cortex_growth_logs").insert({
        "decision_context": "SDK Model Availability Check",
        "options_provided": {"discovery": "gemini-2.5-flash verified via SDK list"},
        "user_choice": "Hot-swapped into fallback priority",
        "ai_prediction": "Only 1.5, 2.0, and 3.0 series were production-ready",
        "prediction_match": False,
        "lessons_learned": "Always check client.models.list() for newly enabled free-tier models. Gemini 2.5-flash provided emergency capacity when all other 'stable' models hit 429."
    }).execute()
    
    print("[OK] Growth logs updated with technical post-mortems and 2.5 series discovery.")

if __name__ == "__main__":
    log_error()
