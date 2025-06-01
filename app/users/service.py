from fastapi import Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime, timezone
from app.core.database import get_db
from app.users.models import User
from app.users.schemas import UserCreate, UserResponse, UserUpdate
from app.core.security import get_password_hash
from app.core.exceptions import (
    BadRequestException,
    UnauthorizedException,
    NotFoundException,
)
from .roles import RoleEnum


def create_user(db: Session, user_data: UserCreate) -> User:
    if db.query(User).filter(User.email == user_data.email).first():
        raise BadRequestException("Email already registered")

    try:
        new_user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
            role=RoleEnum.CUSTOMER,  # Default role is USER
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise BadRequestException(f"Failed to create user: {str(e)}")


def get_user(user_id: int, db: Session) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException(f"User with id {user_id} not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        role=user.role,
    )


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[UserResponse]:
    users = (
        db.query(User).options(joinedload(User.role)).offset(skip).limit(limit).all()
    )
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            role=user.role,
        )
        for user in users
    ]


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> UserResponse:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise NotFoundException(f"User with id {user_id} not found")

    update_data = user_update.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != db_user.email:
        if (
            db.query(User)
            .filter(User.email == update_data["email"], User.id != user_id)
            .first()
        ):
            raise BadRequestException(
                f"Email '{update_data['email']}' is already registered by another user."
            )
        db_user.email = update_data["email"]

    if "is_active" in update_data:
        db_user.is_active = update_data["is_active"]

    # Update timestamp
    db_user.updated_at = datetime.now(timezone.utc)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserResponse.model_validate(db_user)


def delete_user(db: Session, user_id: int) -> None:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise NotFoundException(f"User with id {user_id} not found")

    db_user.is_active = False
    db.commit()
    return None
