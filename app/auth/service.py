from jose import JWTError
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.models import RefreshToken
from app.users.models import User
from app.core.security import (
    create_token_pair,
    decode_token,
    verify_password,
    create_access_token,
)
from app.core.exceptions import NotFoundException, UnauthorizedException
from datetime import datetime, timedelta, timezone
from app.core import db_connection

db: Session = db_connection.session

def authenticate_user(email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedException("Incorrect email or password")
    return user


def login_user(form_data: OAuth2PasswordRequestForm):
    user = authenticate_user(form_data.username, form_data.password)
    access_token = create_token_pair(user.id)
    
    save_refresh_token(access_token.refresh_token, user.id)
    
    return access_token


def refresh_token(token: str):
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


def save_refresh_token(token: str, user_id: int):
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    db_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()
