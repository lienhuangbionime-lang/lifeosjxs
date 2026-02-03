from pydantic import BaseModel, Field
from typing import List, Optional

# ==========================================
# 1. 基礎原子結構 (Atomic Structures)
# ==========================================

class TaskItem(BaseModel):
    """
    從日誌中提取的具體行動
    """
    title: str = Field(
        ..., 
        description="任務的具體名稱，必須是可執行的行動"
    )
    status: str = Field(
        "PENDING", 
        description="預設狀態，通常為 PENDING"
    )
    is_urgent: bool = Field(
        False, 
        description="根據上下文判斷是否需要緊急處理"
    )
    context: Optional[str] = Field(
        None, 
        description="任務相關的背景資訊或專案標籤 (如 #coding, #health)"
    )

class ThoughtTrace(BaseModel):
    """
    [關鍵] 思維簽名 (Thought Signature)
    強制 AI 在給出結果前先進行邏輯推演
    """
    observation: str = Field(
        ..., 
        description="客觀觀察：使用者輸入了什麼？有哪些關鍵字？語氣如何？"
    )
    reasoning: str = Field(
        ..., 
        description="邏輯推論：這代表了什麼情緒？與過去的目標有何關聯？"
    )
    critical_check: str = Field(
        ..., 
        description="自我審查：有沒有遺漏的任務？是否過度解讀？"
    )

class MetaMetrics(BaseModel):
    """
    量化指標 (Quantified Self)
    """
    mood: int = Field(..., description="情緒指數 (1-10)，1為最低落，10為最亢奮")
    focus: int = Field(..., description="專注指數 (1-10)，1為分心，10為心流狀態")
    energy: int = Field(..., description="能量指數 (1-10)，1為疲憊，10為充沛")
    tags: List[str] = Field(..., description="從內容提取的主題標籤 (不含 #)")

# ==========================================
# 2. Sorter Agent 輸出結構 (Log Ingestion)
# ==========================================

class LogAnalysisResult(BaseModel):
    """
    用於 /api/v1/ingest
    將雜亂的日記轉化為結構化資料
    """
    # 1. 潛意識思考 (這部分不會顯示給使用者，但會存入 DB 用於除錯)
    thought_trace: ThoughtTrace

    # 2. 顯意識內容 (User Interface)
    summary: str = Field(
        ..., 
        description="一句話總結這篇日誌的核心精神 (用於列表顯示)"
    )
    markdown_body: str = Field(
        ..., 
        description="整理後的 Markdown 格式內容，包含重點摘要與排版，去除冗言贅字"
    )
    
    # 3. 結構化數據 (Database)
    meta: MetaMetrics
    tasks: List[TaskItem] = Field(
        default_factory=list, 
        description="從內容中識別出的所有待辦事項"
    )

# ==========================================
# 3. Architect Agent 輸出結構 (Chat/Advice)
# ==========================================

class ArchitectResponse(BaseModel):
    """
    用於對話系統與建議
    """
    thought_signature: ThoughtTrace
    
    final_reply: str = Field(
        ..., 
        description="給使用者的最終回應，語氣需溫暖、具備洞察力，並符合 LifeOS 的人格設定"
    )
    suggested_actions: List[str] = Field(
        ..., 
        description="3 個具體的後續行動建議 (Next Steps)"
    )
