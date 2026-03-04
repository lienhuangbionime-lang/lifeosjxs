import os
import asyncio
from dotenv import load_dotenv

load_dotenv("c:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")

async def test_embed():
    from google.genai import client, types
    c = client.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    try:
        # First try embedding-001 without dimensionality
        res = c.models.embed_content(
            model="models/gemini-embedding-001",
            contents="test",
        )
        vec = res.embeddings[0].values
        print("Success without dim param. Length:", len(vec))
    except Exception as e:
        print("Error no dim:", e)

    try:
        # Now try with dimensionality=3072, see if the model supports it natively
        res2 = c.models.embed_content(
            model="models/gemini-embedding-001",
            contents="test",
            config=types.EmbedContentConfig(output_dimensionality=3072)
        )
        print("Success with dim param. Length:", len(res2.embeddings[0].values))
    except Exception as e:
        print("Error with dim:", e)

if __name__ == "__main__":
    asyncio.run(test_embed())
