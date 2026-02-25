import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diagnostic")

def test_models():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # Exact IDs from client.models.list()
    models = [
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-flash-lite-latest",
        "gemini-flash-latest",
        "gemini-pro-latest"
    ]
    
    for m in models:
        logger.info(f"Testing model: {m}")
        try:
            resp = client.models.generate_content(
                model=m,
                contents="ping"
            )
            logger.info(f"[OK] {m} is available. Response: {resp.text}")
        except Exception as e:
            logger.error(f"[FAIL] {m}: {e}")

if __name__ == "__main__":
    test_models()
