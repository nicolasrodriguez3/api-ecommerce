from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.service import login_user, refresh_token as refresh_token_service
from app.auth.schemas import RefreshToken, Token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    return login_user(form_data, db)


@router.post("/refresh", response_model=RefreshToken)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    return refresh_token_service(refresh_token, db)
