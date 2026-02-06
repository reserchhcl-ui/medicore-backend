from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.auth.models import User


class ChatMessage(Base):
    """Chat message model for storing conversation history."""
    
    __tablename__ = "chat_messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    recipient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Relationships
    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id])
    recipient: Mapped[Optional["User"]] = relationship("User", foreign_keys=[recipient_id])
    
    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, sender_id={self.sender_id}, recipient_id={self.recipient_id})>"
