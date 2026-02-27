import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def check_data():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    # 1. Check Projects
    projects = supabase.table("projects").select("*").eq("status", "active").execute()
    print(f"Active Projects: {len(projects.data)}")
    for p in projects.data:
        print(f" - {p['name']} ({p['progress']}% )")
        
    # 2. Check Tasks
    tasks = supabase.table("tasks").select("*").eq("status", "todo").execute()
    print(f"Todo Tasks: {len(tasks.data)}")
    for t in tasks.data:
        print(f" - {t['title']} (Project ID: {t['project_id']})")
        
    # 3. Check Monthly Review
    reviews = supabase.table("MonthlyReview").select("*").order("year", desc=True).order("month", desc=True).limit(1).execute()
    print(f"Latest Monthly Review: {len(reviews.data)}")
    if reviews.data:
        r = reviews.data[0]
        print(f" - {r['year']}/{r['month']}: {r['summary'][:100]}...")
    else:
        print(" - No monthly review found.")

if __name__ == "__main__":
    check_data()
