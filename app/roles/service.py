from sqlalchemy.orm import Session
from app.roles.models import Role
from app.roles.schemas import RoleCreate
from app.core.exceptions import BadRequestException, NotFoundException

def create_role(db: Session, role_data: RoleCreate) -> Role:
    existing = db.query(Role).filter_by(name=role_data.name).first()
    if existing:
        raise BadRequestException(f"Role '{role_data.name}' already exists")

    role = Role(**role_data.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

def get_roles(db: Session):
    return db.query(Role).all()

def get_role_by_id(role_id: int, db: Session) -> Role:
    role = db.query(Role).filter_by(id=role_id).first()
    if not role:
        raise NotFoundException(f"Role with ID {role_id} not found")
    return role
