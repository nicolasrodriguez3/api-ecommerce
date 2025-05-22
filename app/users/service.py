from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.users.models import User
from app.users.schemas import UserCreate, UserResponse
from app.core.security import get_password_hash
from app.core.exceptions import BadRequestException, UnauthorizedException


def create_user(db: Session, user_data: UserCreate) -> User:
    if (
        db.query(User)
        .filter((User.username == user_data.username) | (User.email == user_data.email))
        .first()
    ):
        raise BadRequestException("Username or email already registered")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        role_id=1,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedException()

    return UserResponse.model_validate(user)
