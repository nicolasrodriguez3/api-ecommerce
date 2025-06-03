from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core import db_connection
from app.auth.service import login_user, refresh_token as refresh_token_service
from app.auth.schemas import RefreshToken, Token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    return login_user(form_data)


@router.post("/refresh", response_model=RefreshToken)
def refresh_token(refresh_token: str):
    return refresh_token_service(refresh_token)
