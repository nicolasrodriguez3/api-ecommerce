from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.service import AuthService
from app.auth.dependencies import get_current_active_user
from app.auth.schemas import Token
from app.users.schemas import UserCreate, UserResponse
from app.users.models import User

router = APIRouter(prefix="/auth", tags=["autenticación"])

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario"""
    auth_service = AuthService(db)
    user = auth_service.create_user(user_data)
    return user

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Inicia sesión y obtiene token de acceso"""
    auth_service = AuthService(db)
    return auth_service.login(form_data.username, form_data.password)

@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene información del usuario autenticado"""
    return current_user