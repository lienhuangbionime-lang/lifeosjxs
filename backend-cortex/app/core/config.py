# backend-cortex/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
import os

class Settings(BaseSettings):
    # 系統設定
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LifeOS Cortex"
    
    # 關鍵金鑰 (允許為空，避免啟動崩潰)
    GEMINI_API_KEY: str = Field(default="", env='GEMINI_API_KEY')
    DATABASE_URL: str = Field(default="postgresql://user:pass@localhost/db", env='DATABASE_URL')
    
    # 模型設定
    MODEL_FAST: str = "gemini-2.0-flash"
    MODEL_SMART: str = "gemini-2.0-pro-exp-02-05"

    # Pydantic v2 配置：讀取 .env
    model_config = SettingsConfigDict(
        env_file=[".env.shared", ".env"], 
        env_file_encoding='utf-8',
        extra='ignore'
    )

@lru_cache()
def get_settings():
    return Settings()
