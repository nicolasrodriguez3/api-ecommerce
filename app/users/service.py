from sqlalchemy.orm import Session
from app.users.models import User
from app.users.schemas import UserCreate
from app.core.security import get_password_hash
from app.core.exceptions import BadRequestException

def create_user(db: Session, user_data: UserCreate) -> User:
    if db.query(User).filter((User.username == user_data.username) | (User.email == user_data.email)).first():
        raise BadRequestException("Username or email already registered")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
