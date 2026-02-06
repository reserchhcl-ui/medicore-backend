from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.modules.knowledge_base.schemas import SOPResponse


# ============== Playlist Schemas ==============

class PlaylistBase(BaseModel):
    """Base playlist schema."""
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None


class PlaylistCreate(PlaylistBase):
    """Schema for creating a new playlist."""
    pass


class PlaylistUpdate(BaseModel):
    """Schema for updating a playlist."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None


class PlaylistSOPResponse(BaseModel):
    """Schema for SOP association in a playlist response."""
    sop_id: int
    order_index: int
    sop: SOPResponse
    
    class Config:
        from_attributes = True


class PlaylistResponse(PlaylistBase):
    """Basic playlist response."""
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PlaylistDetailResponse(PlaylistResponse):
    """Detailed playlist response including ordered SOPs."""
    sops: List[PlaylistSOPResponse]


# ============== Management Schemas ==============

class PlaylistSOPAdd(BaseModel):
    """Schema for adding an SOP to a playlist."""
    sop_id: int
    order_index: Optional[int] = None


# ============== Progress Schemas ==============

class ProgressResponse(BaseModel):
    """Schema for user progress in a playlist."""
    playlist_id: int
    playlist_title: str
    percentage: float
    read_count: int
    total_count: int
