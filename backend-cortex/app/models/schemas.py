# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime


class LogEntrySchema(BaseModel):
    id: Optional[int] = Field(None, description="Primary key (may be set by DB)")
    date: datetime = Field(..., description="Timestamp of the log entry")
    content: Optional[str] = Field(None, description="Free-text content of the memory / diary")
    mood: Optional[int] = Field(None, ge=0, le=10, description="Mood 0-10")
    focus: Optional[int] = Field(None, ge=0, le=10, description="Focus 0-10")
description="Energy 0-10")    energy: Optional[int] = Field(None, ge=0, le=10, 

    class Config:
        orm_mode = True


class SystemStatusResponse(BaseModel):
    status: Literal["ok", "degraded", "offline"] = "ok"
    current_model: str
    model_versions: List[str]
    note: Optional[str] = None


class UpgradeResponse(BaseModel):
    success: bool
    message: Optional[str] = None