from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.dependencies import get_content_creator, get_admin_user
from app.modules.auth.models import User
from app.modules.knowledge_base.models import SOP, SOPStatus
from app.modules.knowledge_base.schemas import (
    SOPCreate, SOPUpdate, SOPResponse, SOPDetailResponse,
    SOPVersionResponse, SOPReadingResponse
)
from app.modules.knowledge_base import service


router = APIRouter(prefix="/sops", tags=["knowledge-base"])


def sop_to_response(sop: SOP) -> SOPResponse:
    """Convert SOP model to response schema."""
    return SOPResponse(
        id=sop.id,
        title=sop.title,
        category=sop.category,
        status=sop.status,
        created_by_id=sop.created_by_id,
        created_at=sop.created_at,
        updated_at=sop.updated_at,
        current_version_number=sop.current_version.version_number if sop.current_version else None
    )


def sop_to_detail_response(sop: SOP) -> SOPDetailResponse:
    """Convert SOP model to detailed response schema."""
    current = sop.current_version
    return SOPDetailResponse(
        id=sop.id,
        title=sop.title,
        category=sop.category,
        status=sop.status,
        created_by_id=sop.created_by_id,
        created_at=sop.created_at,
        updated_at=sop.updated_at,
        current_version_number=current.version_number if current else None,
        content=current.content if current else None,
        versions_count=len(sop.versions)
    )


@router.post("/", response_model=SOPDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_sop(
    sop_data: SOPCreate,
    current_user: User = Depends(get_content_creator),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new Standard Operating Procedure.
    
    - **Requires**: Admin or Gestor role
    - Creates SOP with initial version (v1)
    """
    sop = await service.create_sop(db, sop_data, current_user)
    return sop_to_detail_response(sop)


@router.get("/", response_model=List[SOPResponse])
async def list_sops(
    status: Optional[SOPStatus] = None,
    category: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all SOPs with optional filters.
    
    - **status**: Filter by status (draft, published, archived)
    - **category**: Filter by category
    """
    sops = await service.get_sops(db, status=status, category=category, limit=limit, offset=offset)
    return [sop_to_response(sop) for sop in sops]


@router.get("/search", response_model=List[SOPResponse])
async def search_sops(
    q: str = Query(..., min_length=2, description="Search query"),
    status: Optional[SOPStatus] = None,
    category: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search SOPs by title and content (Full-Text).
    
    - **q**: Search query (minimum 2 characters)
    """
    sops = await service.search_sops(
        db, query=q, status=status, category=category, limit=limit, offset=offset
    )
    return [sop_to_response(sop) for sop in sops]


@router.get("/{sop_id}", response_model=SOPDetailResponse)
async def get_sop(
    sop_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get SOP details with current version content.
    """
    sop = await service.get_sop_by_id(db, sop_id)
    if not sop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOP not found"
        )
    return sop_to_detail_response(sop)


@router.put("/{sop_id}", response_model=SOPDetailResponse)
async def update_sop(
    sop_id: int,
    update_data: SOPUpdate,
    current_user: User = Depends(get_content_creator),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an SOP.
    
    - **Requires**: Admin or Gestor role
    - If content is provided, creates a new version automatically
    """
    sop = await service.get_sop_by_id(db, sop_id)
    if not sop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOP not found"
        )
    
    updated_sop = await service.update_sop(db, sop, update_data, current_user)
    return sop_to_detail_response(updated_sop)


@router.delete("/{sop_id}", response_model=SOPResponse)
async def archive_sop(
    sop_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Archive an SOP (soft delete).
    
    - **Requires**: Admin role
    """
    sop = await service.get_sop_by_id(db, sop_id)
    if not sop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOP not found"
        )
    
    archived_sop = await service.archive_sop(db, sop)
    return sop_to_response(archived_sop)


@router.get("/{sop_id}/versions", response_model=List[SOPVersionResponse])
async def get_sop_versions(
    sop_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get version history for an SOP.
    """
    sop = await service.get_sop_by_id(db, sop_id)
    if not sop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOP not found"
        )
    
    versions = await service.get_sop_versions(db, sop_id)
    return versions


@router.post("/{sop_id}/acknowledge", response_model=SOPReadingResponse, status_code=status.HTTP_201_CREATED)
async def acknowledge_sop(
    sop_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge reading of current SOP version ("Li e Estou Ciente").
    
    - Records timestamp and version for audit
    - Can only acknowledge once per version
    """
    sop = await service.get_sop_by_id(db, sop_id)
    if not sop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOP not found"
        )
    
    if sop.status != SOPStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only acknowledge published SOPs"
        )
    
    try:
        reading = await service.acknowledge_sop(db, sop, current_user)
        return reading
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
