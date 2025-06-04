from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.repository.base import BaseRepository
from app.users.models import User


class UserRepository(BaseRepository[User]):
    """Repositorio de usuarios con consultas específicas."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email."""
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_users(self, *, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtener usuarios activos."""
        stmt = select(User).where(User.is_active == True).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
