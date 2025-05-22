from typing import Annotated
from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.users.models import User
from app.users.roles import RoleEnum


def require_roles(*roles: RoleEnum):
    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ):
        if current_user.role.name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker
