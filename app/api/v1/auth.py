from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.service import AuthService
from app.users.models import UserRole
from app.users.schemas import NewUserCreate, UserCreate, UserResponse
from app.auth.schemas import Token
from app.auth.dependencies import CurrentActiveUser
from app.users.service import UserService

router = APIRouter(prefix="/auth", tags=["autenticación"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: NewUserCreate, db: Annotated[Session, Depends(get_db)]):
    """Registra un nuevo usuario"""
    new_user = UserCreate(
        email=user_data.email, password=user_data.password, roles=[UserRole.CUSTOMER]
    )
    
    user_service = UserService(db)
    user = await user_service.create_user(new_user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    """Inicia sesión y obtiene token de acceso"""
    auth_service = AuthService(db)
    return await auth_service.login(form_data.username, form_data.password)


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: CurrentActiveUser):
    """Refresca el token de acceso"""
    from datetime import timedelta
    from app.auth.utils import create_access_token
    from app.core.config import get_settings

    settings = get_settings()

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.id}, expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token, expires_in=settings.access_token_expire_minutes * 60
    )
