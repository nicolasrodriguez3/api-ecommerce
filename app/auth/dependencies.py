from typing import Annotated
from fastapi import Depends, HTTPException, Path, status

from app.core.security import get_current_user
from app.users.models import User
from app.users.roles import RoleEnum


def require_roles(*roles: RoleEnum):
    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker

def require_self_or_roles(*roles: RoleEnum, user_id_path_param: str = "user_id"):
    def dependency(
        target_user_id: int = Path(..., alias=user_id_path_param), # Use alias for flexibility
        current_user: User = Depends(get_current_user)
    ):
        if current_user.id == target_user_id:
            return current_user # User is accessing their own resource

        # If not self, check if user has one of the specified roles
        # This assumes User model has 'role' attribute which has a 'name' attribute (e.g. RoleEnum.admin.name)
        if hasattr(current_user, 'role') and current_user.role and current_user.role in roles:
            return current_user # User has a permitted role

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action on this resource.",
        )
    return dependency