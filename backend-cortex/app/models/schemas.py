# backend-cortex/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- Request Models ---
class IngestRequest(BaseModel):
    content: str = Field(..., description="Raw text or transcript from CaptureView")
    source: str = Field("web_terminal", description="Source of the input")
    client_timestamp: Optional[str] = None
    anchor_date: Optional[str] = Field(None, description="Override date for historical ingest (YYYY-MM-DD)")
    habits: Optional[List[str]] = []
    skipAi: bool = False
    mode: str = "append"

# --- Response Models ---
class AISortedResult(BaseModel):
    markdown_body: Optional[str] = Field(None, description="Refinement in Markdown")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata including metrics")
    tasks: Optional[List[Dict[str, Any]]] = Field(None, description="Extracted tasks")
    tags: List[str] = []
    graph_seeds: List[str] = []

class IngestResponse(BaseModel):
    success: bool
    model: str
    data: Optional[AISortedResult] = None

class SystemStatusResponse(BaseModel):
    status: str
    current_model: str
    model_versions: List[str]
    api_usage: Optional[Dict[str, int]] = Field(None, description="API usage statistics")
    remaining_requests: Optional[str] = None
    note: Optional[str] = None

class UpgradeResponse(BaseModel):
    success: bool
    message: str

class PromptRequest(BaseModel):
    content: str

class PromptResponse(BaseModel):
    name: str
    content: str
    last_modified: str

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str = "google"
    is_free: bool = True

class ModelListResponse(BaseModel):
    models: List[ModelInfo]

class LogEntrySchema(BaseModel):
    id: Optional[str] = None
    content: str
    date: str
    mood: int = 5
    focus: int = 5
    energy: int = 5
    tags: List[str] = []
    category: str = "Life"
    is_ai: bool = False
    ai_model: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        extra = "ignore"
        from_attributes = True

# --- Project Schemas ---

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = 'active'
    tags: List[str] = []
    meta: Optional[Dict[str, Any]] = {}

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    tags: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None

class ProjectMergeRequest(BaseModel):
    target_project_id: str

# --- Document Schemas ---

class DocumentSchema(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    content: str
    doc_type: str = "webpage"
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentCreate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    content: str
    doc_type: str = "webpage"
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
