import requests
import json

def test_proactive_url():
    url = "http://localhost:8000/api/v1/chat/message"
    payload = {
        "message": "",  # Empty message to trigger proactive directive
        "history": [],
        "url_context": {
            "url": "https://lm-kit.com/blog/agent-skills-explained/",
            "title": "Agent Skills Explained",
            "type": "webpage",
            "content": "Agent Skills are modular, standardized capability handbooks for AI. They solve System Prompt bloat by using progressive disclosure: defining a skill in SKILL.md and only loading it when needed. This allows AI to have professional-grade specialization without context window exhaustion."
        }
    }
    
    print("Testing /api/v1/chat/message with simulated URL context...")
    try:
        response = requests.post(url, json=payload, stream=True)
        print(f"Status: {response.status_code}")
        
        full_response = ""
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                text = chunk.decode("utf-8")
                full_response += text
                print(text, end="", flush=True)
        
        print("\n\n--- Verification ---")
        if "LifeOS" in full_response or "architecture" in full_response.lower():
            print("[OK] Response correctly references LifeOS architecture.")
        if "Directive" not in full_response:
             print("[OK] Internal directive not leaked, but acted upon.")
        else:
             print("[FAIL] Internal directive leaked into output.")
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_proactive_url()
