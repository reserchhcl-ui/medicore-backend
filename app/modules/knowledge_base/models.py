import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.auth.models import User


class SOPStatus(str, enum.Enum):
    """Status of a Standard Operating Procedure."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SOP(Base):
    """Standard Operating Procedure (POP) model."""
    
    __tablename__ = "sops"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[SOPStatus] = mapped_column(
        Enum(SOPStatus), 
        default=SOPStatus.DRAFT, 
        nullable=False
    )
    
    # Author
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
    versions: Mapped[List["SOPVersion"]] = relationship(
        "SOPVersion", 
        back_populates="sop",
        order_by="desc(SOPVersion.version_number)"
    )
    
    @property
    def current_version(self) -> Optional["SOPVersion"]:
        """Get the latest version of this SOP."""
        return self.versions[0] if self.versions else None
    
    def __repr__(self) -> str:
        return f"<SOP(id={self.id}, title={self.title}, status={self.status})>"


class SOPVersion(Base):
    """Version history for SOP content."""
    
    __tablename__ = "sop_versions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sop_id: Mapped[int] = mapped_column(ForeignKey("sops.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Who created this version
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Relationships
    sop: Mapped["SOP"] = relationship("SOP", back_populates="versions")
    readings: Mapped[List["SOPReading"]] = relationship("SOPReading", back_populates="sop_version")
    
    def __repr__(self) -> str:
        return f"<SOPVersion(sop_id={self.sop_id}, version={self.version_number})>"


class SOPReading(Base):
    """Audit log for SOP acknowledgments (Li e Estou Ciente)."""
    
    __tablename__ = "sop_readings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sop_version_id: Mapped[int] = mapped_column(
        ForeignKey("sop_versions.id", ondelete="CASCADE"), 
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Timestamp of acknowledgment
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Relationships
    sop_version: Mapped["SOPVersion"] = relationship("SOPVersion", back_populates="readings")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        return f"<SOPReading(user_id={self.user_id}, version_id={self.sop_version_id})>"
