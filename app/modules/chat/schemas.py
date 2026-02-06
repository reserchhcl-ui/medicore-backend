from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """Base schema for chat messages."""
    content: str = Field(..., min_length=1)
    recipient_id: Optional[int] = None


class MessageCreate(MessageBase):
    """Schema for sending a new message (usually via WebSocket)."""
    pass


class MessageResponse(MessageBase):
    """Detailed message response schema."""
    id: int
    sender_id: int
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatPartnerResponse(BaseModel):
    """Schema for a person the user has a conversation with."""
    user_id: int
    full_name: str
    last_message: str
    last_message_time: datetime
    unread_count: int = 0
    is_online: bool = False
