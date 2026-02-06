from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by email address.
    
    Args:
        db: Database session.
        email: User's email address.
    
    Returns:
        User if found, None otherwise.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        db: Database session.
        user_id: User's ID.
    
    Returns:
        User if found, None otherwise.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session.
        user_data: User creation data.
    
    Returns:
        Created user instance.
    """
    hashed_password = get_password_hash(user_data.password)
    
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
    )
    
    db.add(user)
    await db.flush()
    await db.refresh(user)
    
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session.
        email: User's email address.
        password: Plain text password.
    
    Returns:
        User if credentials are valid, None otherwise.
    """
    user = await get_user_by_email(db, email)
    
    if user is None:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    if not user.is_active:
        return None
    
    return user
