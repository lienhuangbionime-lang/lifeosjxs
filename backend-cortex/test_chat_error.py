import asyncio
import httpx
import traceback

async def test():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "http://localhost:8000/api/v1/chat/message",
                json={"message": "test", "history": [], "model": "models/gemini-2.0-flash"},
            )
            print("STATUS:", resp.status_code)
            print("BODY:", resp.text[:500])
    except Exception as e:
        traceback.print_exc()

asyncio.run(test())
