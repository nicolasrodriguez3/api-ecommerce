from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.users.service import UserService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependencia para obtener servicio de usuarios."""
    return UserService(db)