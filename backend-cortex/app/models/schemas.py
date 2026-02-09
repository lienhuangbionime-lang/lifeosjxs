# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime


class LogEntrySchema(BaseModel):
    id: Optional[int] = Field(None, description="Primary key (may be set by DB)")
    date: datetime = Field(..., description="Timestamp of the log entry")
    content: Optional[str] = Field(None, description="Free-text content of the memory / diary")
    mood: Optional[int] = Field(None, ge=0, le=10, description="Mood 0-10")
    focus: Optional[int] = Field(None, ge=0, le=10, description="Focus 0-10")
    energy: Optional[int] = Field(None, ge=0, le=10, description="Energy 0-10")
    
    # New Fields for LifeOS v7
    isAi: Optional[bool] = False
    aiModel: Optional[str] = None
    habits: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []
    meta: Optional[Dict[str, Any]] = {}

    class Config:
        orm_mode = True


class ProjectSchema(BaseModel):
    id: Optional[int] = Field(None, description="Primary Key")
    created_at: Optional[datetime] = None
    name: str
    status: Literal["active", "archived", "completed", "idea"] = "active"
    progress: int = Field(0, ge=0, le=100)
    meta: Dict[str, Any] = Field(default_factory=dict, description="UI Metadata: vibe, emoji, cover_image")
    tags: List[str] = Field(default_factory=list)

    class Config:
        orm_mode = True


class SystemStatusResponse(BaseModel):
    status: Literal["ok", "degraded", "offline"] = "ok"
    current_model: str
    model_versions: List[str]
    remaining_requests: Optional[str] = None
    note: Optional[str] = None


class UpgradeResponse(BaseModel):
    success: bool
    message: Optional[str] = None