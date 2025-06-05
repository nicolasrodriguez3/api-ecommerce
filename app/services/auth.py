from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import Token
from app.core.security import (
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Autentica usuario por email y contraseña"""
        user = await self.user_repo.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    async def login(self, email: str, password: str) -> Token:
        """Realiza login y retorna token"""
        user = await self.authenticate_user(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo"
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
        )
