from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.dependencies import get_content_creator
from app.modules.auth.models import User
from app.modules.onboarding.schemas import (
    PlaylistCreate, PlaylistUpdate, PlaylistResponse, 
    PlaylistDetailResponse, PlaylistSOPAdd, ProgressResponse
)
from app.modules.onboarding import service


router = APIRouter(prefix="/playlists", tags=["onboarding"])


@router.post("/", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist_data: PlaylistCreate,
    current_user: User = Depends(get_content_creator),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new playlist.
    - **Requires**: Admin or Gestor role.
    """
    playlist = await service.create_playlist(db, playlist_data, current_user)
    return playlist


@router.get("/", response_model=List[PlaylistResponse])
async def list_playlists(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all playlists."""
    playlists = await service.get_playlists(db, limit=limit, offset=offset)
    return playlists


@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
async def get_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get playlist details including its SOPs."""
    playlist = await service.get_playlist_by_id(db, playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    return playlist


@router.put("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: int,
    update_data: PlaylistUpdate,
    current_user: User = Depends(get_content_creator),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a playlist.
    - **Requires**: Admin or Gestor role.
    """
    playlist = await service.get_playlist_by_id(db, playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    updated = await service.update_playlist(db, playlist, update_data)
    return updated


@router.post("/{playlist_id}/sops", status_code=status.HTTP_201_CREATED)
async def add_sop_to_playlist(
    playlist_id: int,
    data: PlaylistSOPAdd,
    current_user: User = Depends(get_content_creator),
    db: AsyncSession = Depends(get_db)
):
    """
    Add an SOP to a playlist.
    - **Requires**: Admin or Gestor role.
    """
    playlist = await service.get_playlist_by_id(db, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    await service.add_sop_to_playlist(db, playlist_id, data.sop_id, data.order_index)
    return {"status": "success", "message": "SOP added to playlist"}


@router.delete("/{playlist_id}/sops/{sop_id}")
async def remove_sop_from_playlist(
    playlist_id: int,
    sop_id: int,
    current_user: User = Depends(get_content_creator),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove an SOP from a playlist.
    - **Requires**: Admin or Gestor role.
    """
    success = await service.remove_sop_from_playlist(db, playlist_id, sop_id)
    if not success:
        raise HTTPException(status_code=404, detail="Association not found")
    return {"status": "success", "message": "SOP removed from playlist"}


@router.get("/{playlist_id}/progress", response_model=ProgressResponse)
async def get_playlist_progress(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate progress for the current user in a playlist.
    """
    progress = await service.calculate_progress(db, current_user.id, playlist_id)
    return ProgressResponse(
        playlist_id=playlist_id,
        playlist_title=progress["title"],
        percentage=progress["percentage"],
        read_count=progress["read_count"],
        total_count=progress["total_count"]
    )
