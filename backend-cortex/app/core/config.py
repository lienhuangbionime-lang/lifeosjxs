from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # 定義變數 (Pydantic 會自動從環境變數讀取)
    GEMINI_API_KEY: str
    MODEL_SMART: str = "models/gemini-3-pro-preview"

    # [CTO 關鍵修復] 明確指定 .env 檔案路徑
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # 忽略多餘的變數
    )

settings = Settings()
