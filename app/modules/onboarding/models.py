from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.auth.models import User
    from app.modules.knowledge_base.models import SOP


class Playlist(Base):
    """Playlist (Trilha) model for grouping SOPs in a logical order."""
    
    __tablename__ = "playlists"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Creator
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    sops: Mapped[List["PlaylistSOP"]] = relationship(
        "PlaylistSOP", 
        back_populates="playlist",
        order_by="PlaylistSOP.order_index",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Playlist(id={self.id}, title={self.title})>"


class PlaylistSOP(Base):
    """Association model between Playlists and SOPs with ordering."""
    
    __tablename__ = "playlist_sops"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    playlist_id: Mapped[int] = mapped_column(ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    sop_id: Mapped[int] = mapped_column(ForeignKey("sops.id", ondelete="CASCADE"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    playlist: Mapped["Playlist"] = relationship("Playlist", back_populates="sops")
    sop: Mapped["SOP"] = relationship("SOP")
    
    def __repr__(self) -> str:
        return f"<PlaylistSOP(playlist_id={self.playlist_id}, sop_id={self.sop_id}, order={self.order_index})>"
