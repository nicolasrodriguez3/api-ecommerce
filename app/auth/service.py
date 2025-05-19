from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.users.models import User
from app.core.security import verify_password, create_access_token
from app.core.exceptions import UnauthorizedException
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
