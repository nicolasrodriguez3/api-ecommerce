
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.user import Role, UserRole

class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: UserRole) -> Optional[Role]:
        return self.db.query(Role).filter(Role.name == name).first()

    def get_or_create(self, name: UserRole, description: str | None = None) -> Role:
        role = self.get_by_name(name)
        if not role:
            role = Role(name=name, description=description)
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)
        return role

    def get_all(self) -> List[Role]:
        return self.db.query(Role).all()


