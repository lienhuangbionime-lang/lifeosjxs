import os
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

async def test_2_5():
    if not api_key:
        print("Error: GEMINI_API_KEY missing")
        return
    
    client = genai.Client(api_key=api_key)
    print("Testing models/gemini-2.5-flash...")
    try:
        response = await client.aio.models.generate_content(
            model="models/gemini-2.5-flash",
            contents="Confirming connectivity. Respond with 'READY'.",
            config=types.GenerateContentConfig(max_output_tokens=5)
        )
        print(f"Response: {response.text.strip()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_2_5())
