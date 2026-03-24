import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def probe():
    if not api_key:
        print("Error: GEMINI_API_KEY missing")
        return
    
    client = genai.Client(api_key=api_key)
    print("Available Models:")
    print("-" * 30)
    try:
        for m in client.models.list():
            print(f"- {m.name} (Supported: {m.supported_actions})")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    probe()
