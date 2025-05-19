from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.roles.schemas import RoleCreate, RoleResponse
from app.roles import service

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("/", response_model=RoleResponse)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    return service.create_role(db, role)


@router.get("/", response_model=list[RoleResponse])
def list_roles(db: Session = Depends(get_db)):
    return service.get_roles(db)
