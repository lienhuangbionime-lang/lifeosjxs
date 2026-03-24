from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

class MenuItem(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    is_soul_food: bool = False

class NomadMenu(BaseModel):
    items: List[MenuItem]
    source_url: Optional[str] = None
    digitized_at: datetime = Field(default_factory=datetime.now)

class NomadEntity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    cuisine: Optional[str] = None
    trust_score: int = 0
    distance_text: Optional[str] = None
    image_url: Optional[str] = None
    has_soul_bond: bool = False
    is_never_visited: bool = True
    is_synced: bool = False
    vibe_tags: List[str] = []
    diet_type: Optional[str] = None
    source: str = "manual"
    place_id: Optional[str] = None
    menu_data: List[MenuItem] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True
