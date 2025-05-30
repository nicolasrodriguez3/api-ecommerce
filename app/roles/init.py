from sqlalchemy.orm import Session
from app.roles.models import Role
from app.users.roles import RoleEnum

DEFAULT_ROLES = RoleEnum.__members__.values()

def init_roles(db: Session):
    for role_name in DEFAULT_ROLES:
        exists = db.query(Role).filter_by(name=role_name).first()
        if not exists:
            db.add(Role(name=role_name))
    db.commit()
