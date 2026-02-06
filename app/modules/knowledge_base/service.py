from typing import Optional, List

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.models import User
from app.modules.knowledge_base.models import SOP, SOPVersion, SOPReading, SOPStatus
from app.modules.knowledge_base.schemas import SOPCreate, SOPUpdate


async def create_sop(db: AsyncSession, sop_data: SOPCreate, user: User) -> SOP:
    """
    Create a new SOP with initial version.
    
    Args:
        db: Database session.
        sop_data: SOP creation data.
        user: Current user (creator).
    
    Returns:
        Created SOP with version 1.
    """
    # Create the SOP
    sop = SOP(
        title=sop_data.title,
        category=sop_data.category,
        status=sop_data.status,
        created_by_id=user.id,
    )
    db.add(sop)
    await db.flush()
    
    # Create initial version
    version = SOPVersion(
        sop_id=sop.id,
        version_number=1,
        content=sop_data.content,
        change_summary="Versão inicial",
        created_by_id=user.id,
    )
    db.add(version)
    await db.flush()
    
    # Refresh to load relationships
    await db.refresh(sop, ["versions"])
    return sop


async def get_sop_by_id(db: AsyncSession, sop_id: int) -> Optional[SOP]:
    """Get SOP by ID with versions loaded."""
    result = await db.execute(
        select(SOP)
        .options(selectinload(SOP.versions))
        .where(SOP.id == sop_id)
    )
    return result.scalar_one_or_none()


async def get_sops(
    db: AsyncSession, 
    status: Optional[SOPStatus] = None,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[SOP]:
    """Get list of SOPs with optional filters."""
    query = select(SOP).options(selectinload(SOP.versions))
    
    if status:
        query = query.where(SOP.status == status)
    if category:
        query = query.where(SOP.category == category)
    
    query = query.order_by(SOP.updated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_sop(
    db: AsyncSession, 
    sop: SOP, 
    update_data: SOPUpdate, 
    user: User
) -> SOP:
    """
    Update SOP. If content changes, creates a new version.
    
    Args:
        db: Database session.
        sop: Existing SOP to update.
        update_data: Update data.
        user: Current user.
    
    Returns:
        Updated SOP.
    """
    # Update basic fields
    if update_data.title is not None:
        sop.title = update_data.title
    if update_data.category is not None:
        sop.category = update_data.category
    if update_data.status is not None:
        sop.status = update_data.status
    
    # If content changed, create new version
    if update_data.content is not None:
        current_version = sop.current_version
        new_version_number = (current_version.version_number + 1) if current_version else 1
        
        new_version = SOPVersion(
            sop_id=sop.id,
            version_number=new_version_number,
            content=update_data.content,
            change_summary=update_data.change_summary,
            created_by_id=user.id,
        )
        db.add(new_version)
    
    await db.flush()
    await db.refresh(sop, ["versions"])
    return sop


async def get_sop_versions(db: AsyncSession, sop_id: int) -> List[SOPVersion]:
    """Get all versions of an SOP."""
    result = await db.execute(
        select(SOPVersion)
        .where(SOPVersion.sop_id == sop_id)
        .order_by(SOPVersion.version_number.desc())
    )
    return list(result.scalars().all())


async def get_version_by_id(db: AsyncSession, version_id: int) -> Optional[SOPVersion]:
    """Get specific version by ID."""
    result = await db.execute(
        select(SOPVersion).where(SOPVersion.id == version_id)
    )
    return result.scalar_one_or_none()


async def acknowledge_sop(db: AsyncSession, sop: SOP, user: User) -> SOPReading:
    """
    Record that user has read and acknowledged current version of SOP.
    
    Args:
        db: Database session.
        sop: SOP to acknowledge.
        user: Current user.
    
    Returns:
        Reading record.
    """
    current_version = sop.current_version
    if not current_version:
        raise ValueError("SOP has no versions")
    
    # Check if already acknowledged this version
    existing = await db.execute(
        select(SOPReading)
        .where(SOPReading.sop_version_id == current_version.id)
        .where(SOPReading.user_id == user.id)
    )
    if existing.scalar_one_or_none():
        raise ValueError("Already acknowledged this version")
    
    reading = SOPReading(
        sop_version_id=current_version.id,
        user_id=user.id,
    )
    db.add(reading)
    await db.flush()
    await db.refresh(reading)
    return reading


async def get_user_readings(db: AsyncSession, user_id: int) -> List[SOPReading]:
    """Get all reading records for a user."""
    result = await db.execute(
        select(SOPReading)
        .options(selectinload(SOPReading.sop_version))
        .where(SOPReading.user_id == user_id)
        .order_by(SOPReading.acknowledged_at.desc())
    )
    return list(result.scalars().all())


async def search_sops(
    db: AsyncSession,
    query: str,
    status: Optional[SOPStatus] = None,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[SOP]:
    """
    Search SOPs by title and content (Full-Text).
    
    For SQLite: uses LIKE
    For PostgreSQL: would use to_tsvector/to_tsquery
    """
    search_pattern = f"%{query}%"
    
    # Get SOPs where title matches or latest version content matches
    stmt = (
        select(SOP)
        .options(selectinload(SOP.versions))
        .outerjoin(SOPVersion)
        .where(
            or_(
                SOP.title.ilike(search_pattern),
                SOPVersion.content.ilike(search_pattern)
            )
        )
        .distinct()
    )
    
    if status:
        stmt = stmt.where(SOP.status == status)
    if category:
        stmt = stmt.where(SOP.category == category)
    
    stmt = stmt.order_by(SOP.updated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def archive_sop(db: AsyncSession, sop: SOP) -> SOP:
    """Archive an SOP (soft delete)."""
    sop.status = SOPStatus.ARCHIVED
    await db.flush()
    return sop
