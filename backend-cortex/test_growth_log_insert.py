import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("c:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Missing SUPABASE credentials")
    exit(1)

supabase = create_client(url, key)

test_record = {
    "decision_context": "Testing the cortex_growth_logs writing capability",
    "options_provided": {"A": "Write to DB", "B": "Do not write"},
    "user_choice": "A",
    "ai_prediction": "A",
    "prediction_match": True,
    "lessons_learned": "The database connection is working."
}

try:
    res = supabase.table("cortex_growth_logs").insert(test_record).execute()
    print("Success:", res.data)
except Exception as e:
    print("Error:", e)
