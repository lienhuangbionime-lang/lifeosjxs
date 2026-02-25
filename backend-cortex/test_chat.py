import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_backend")

BASE_URL = "http://127.0.0.1:8000"

def test_chat():
    logger.info("Testing /api/v1/chat/message...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/message",
            json={
                "message": "這篇文章在說什麼",
                "history": [],
                "model": "models/gemini-flash-lite-latest",
                "url_context": {
                    "url": "https://example.com/ai-research",
                    "type": "webpage",
                    "title": "AI in Research",
                    "content": "This is a short article about AI accelerating research.",
                    "summary": "AI accelerates research."
                }
            },
            stream=True
        )
        if response.status_code == 200:
            logger.info("[OK] Chat Endpoint returned 200. Reading stream...")
            output = ""
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    output += chunk.decode('utf-8')
            logger.info(f"Response snippet: {output[:100]}...")
        else:
            logger.error(f"[ERROR] Chat Endpoint Failed: {response.status_code} - {response.text}")
    except Exception as e:
         logger.error(f"[ERROR] Connection Failed: {e}")

if __name__ == "__main__":
    test_chat()
