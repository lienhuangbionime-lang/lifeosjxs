import logging
from typing import List
from app.core.gemini import get_gemini_client
from google.genai import types
from skills.e_nav.schema import NomadMenu

logger = logging.getLogger("cortex.enav.vision")

async def digitize_menu_with_gemini_3(image_data: bytes) -> NomadMenu:
    """
    Uses Gemini 3.0 Flash to digitize a menu image.
    Transfers image bytes into structured items.
    """
    client = get_gemini_client()
    if not client:
        logger.error("Gemini client not configured. Check GEMINI_API_KEY.")
        raise RuntimeError("Gemini client not initialized")

    prompt = """
    你是一位專業的數位菜單建模師。請分析這張菜單圖片，並提取所有菜品資訊。
    輸出格式必須嚴格遵守提供的 JSON Schema。
    
    規則：
    1. 提取所有菜名 (name) 與價格 (price)。
    2. 如果菜品看起來是明星產品、招牌菜或是圖片中特別標註的，請將 is_soul_food 設為 true。
    3. 價格請轉換為純數字（台幣 TWD）。
    4. 語言：繁體中文。
    """

    try:
        # The user specifically requested Gemini 3.0 Flash
        # Note: If the SDK/Backend doesn't support this ID yet, it will fail over to the safe handler
        logger.info("Deploying Gemini 3.0 Flash for Menu Digitization...")
        
        response = await client.aio.models.generate_content(
            model="gemini-3.0-flash",
            contents=[
                prompt,
                types.Part.from_bytes(data=image_data, mime_type="image/jpeg")
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=NomadMenu.model_json_schema()
            )
        )
        
        if not response.text:
            raise ValueError("Empty response from Gemini 3.0 Flash")
            
        return NomadMenu.model_validate_json(response.text)
        
    except Exception as e:
        logger.error(f"Gemini 3.0 Menu Digitization failed: {e}")
        # Fallback logic could go here if needed
        raise e
