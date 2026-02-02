from pydantic import BaseModel, Field
from typing import List, Optional

class LogEntry(BaseModel):
    """將使用者的輸入轉化為結構化日誌"""
    category: str = Field(..., description="分類標籤 (e.g., Work, Life, Idea)")
    tags: List[str] = Field(..., description="相關標籤")
    summary: str = Field(..., description="一句話總結")
    mood_score: int = Field(..., description="情緒分數 1-10", ge=1, le=10)
    action_items: List[str] = Field(default=[], description="需要執行的下一步行動")
