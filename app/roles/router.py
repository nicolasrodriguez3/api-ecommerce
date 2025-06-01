from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.roles.schemas import RoleCreate, RoleResponse
from app.roles import service

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/")
def list_roles() -> list[str]:
    return service.get_roles()
