from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.modules.knowledge_base.models import SOPStatus


# ============== SOP Schemas ==============

class SOPBase(BaseModel):
    """Base SOP schema."""
    title: str = Field(..., min_length=3, max_length=255)
    category: Optional[str] = Field(None, max_length=100)


class SOPCreate(SOPBase):
    """Schema for creating a new SOP."""
    content: str = Field(..., min_length=1, description="Initial content for version 1")
    status: SOPStatus = SOPStatus.DRAFT


class SOPUpdate(BaseModel):
    """Schema for updating an SOP (creates new version)."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = Field(None, min_length=1)
    status: Optional[SOPStatus] = None
    change_summary: Optional[str] = Field(None, max_length=500, description="Summary of changes")


class SOPVersionResponse(BaseModel):
    """Schema for SOP version response."""
    id: int
    version_number: int
    content: str
    change_summary: Optional[str]
    created_by_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SOPResponse(SOPBase):
    """Schema for SOP list response."""
    id: int
    status: SOPStatus
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    current_version_number: Optional[int] = None
    
    class Config:
        from_attributes = True


class SOPDetailResponse(SOPResponse):
    """Schema for SOP detail response with current content."""
    content: Optional[str] = None
    versions_count: int = 0


# ============== Reading/Acknowledgment Schemas ==============

class SOPReadingCreate(BaseModel):
    """Schema for acknowledging an SOP."""
    pass  # No additional fields needed, user comes from auth


class SOPReadingResponse(BaseModel):
    """Schema for SOP reading response."""
    id: int
    sop_version_id: int
    user_id: int
    acknowledged_at: datetime
    
    class Config:
        from_attributes = True


class UserReadingStatus(BaseModel):
    """Schema showing user's reading status for an SOP."""
    sop_id: int
    sop_title: str
    has_read_current_version: bool
    last_read_version: Optional[int] = None
    last_read_at: Optional[datetime] = None
    current_version: int


# ============== Search Schema ==============

class SOPSearchParams(BaseModel):
    """Schema for SOP search parameters."""
    q: str = Field(..., min_length=2, description="Search query")
    category: Optional[str] = None
    status: Optional[SOPStatus] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
