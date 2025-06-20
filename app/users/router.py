from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import db_connection
from app.auth.dependencies import get_current_user
from app.users.roles import RoleEnum
from app.users.schemas import UserCreate, UserResponse, UserUpdate
from app.users.service import (
    create_user as service_create_user,
    get_user as service_get_user,
    get_users as service_get_users,
    update_user as service_update_user,
    delete_user as service_delete_user,
)
from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.users.models import User

router = APIRouter(prefix="/users", tags=["Users"])

db: Session = db_connection.session

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the details of the currently authenticated user.
    """
    return current_user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_new_user(user: UserCreate):
    """
    Create a new user.

    Handles username and email duplication checks via the service layer.
    """
    return service_create_user(user_data=user)


@router.get("/", response_model=List[UserResponse])
def read_users_list(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a list of users.

    - Accessible only by admin users (role_id = 1).
    - Supports pagination using `skip` and `limit` query parameters.
    """
    if current_user.role != RoleEnum.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )
    users = service_get_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a specific user by their ID.

    - Admin users can retrieve any user.
    - Regular users can only retrieve their own data.
    """
    # Allow user to get their own data or admin to get any user's data
    if current_user.id != user_id and current_user.role != RoleEnum.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's data",
        )
    try:
        user = service_get_user(user_id=user_id, db=db)
        return user
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
def update_existing_user(
    user_id: int,
    user_update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update a user's details by their ID.

    - Admin users can update any user.
    - Regular users can only update their own data.
    - Username and email uniqueness are checked by the service layer.
    """
    # Allow user to update their own data or admin to update any user's data
    if current_user.id != user_id and current_user.role != RoleEnum.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )

    return service_update_user(user_id=user_id, user_update=user_update_data)


@router.delete("/{user_id}", response_model=None, status_code=204)
def delete_existing_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a user by their ID.

    - Accessible only by admin users (role_id = 1).
    """
    if current_user.role != RoleEnum.ADMIN.value:
        raise ForbiddenException("Not authorized to delete users")
    try:
        return service_delete_user(user_id=user_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
