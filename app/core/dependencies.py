from typing import List

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.modules.auth.models import User, UserRole


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory that requires user to have one of the specified roles.
    
    Usage:
        @router.post("/", dependencies=[Depends(require_roles([UserRole.ADMIN]))])
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker


# Convenience dependencies
require_admin = require_roles([UserRole.ADMIN])
require_admin_or_gestor = require_roles([UserRole.ADMIN, UserRole.GESTOR])
require_any_role = require_roles([UserRole.ADMIN, UserRole.GESTOR, UserRole.COLABORADOR])


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that requires admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_content_creator(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that requires admin or gestor role (can create/edit content)."""
    if current_user.role not in [UserRole.ADMIN, UserRole.GESTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Gestor access required"
        )
    return current_user
