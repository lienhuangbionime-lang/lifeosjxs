from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class LogEntry(BaseModel):
    content: str = Field(..., description="The main text content of the entry")
    date: Optional[str] = Field(None, description="ISO 8601 formatted date string if mentioned, or null")
    mood: Optional[int] = Field(None, description="Mood rating (0-10) if explicitly mentioned or strongly implied")
    focus: Optional[int] = Field(None, description="Focus rating (0-10) if explicitly mentioned or strongly implied")
    energy: Optional[int] = Field(None, description="Energy rating (0-10) if explicitly mentioned or strongly implied")
    tags: List[str] = Field(default_factory=list, description="List of tags relevant to the entry")
    category: Optional[str] = Field(None, description="Derived category: e.g., 'Journal', 'Idea', 'Task', 'Learning'")
    projects: List[str] = Field(default_factory=list, description="List of project names detected in the entry")
    is_private: bool = Field(default=False, description="Whether the entry is private/family and should not be uploaded to cloud")
    facts: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence facts for scoring engine")

