from jose import JWTError
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.users.models import User
from app.core.security import decode_token, verify_password, create_access_token
from app.core.exceptions import NotFoundException, UnauthorizedException
from datetime import timedelta

def authenticate_user(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedException("Incorrect email or password")
    return user

def login_user(form_data: OAuth2PasswordRequestForm, db: Session):
    user = authenticate_user(form_data.username, form_data.password, db)
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


def refresh_token(token: str, db: Session):
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")
        
        user_id: int | None = payload.get("sub")
    except (JWTError, ValueError):
        raise UnauthorizedException("Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User not found")

    new_access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": new_access_token, "token_type": "bearer"}