from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import Role, User, UserRole
from app.repositories.base import BaseRepository
from app.repositories.role import RoleRepository
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy.exc import IntegrityError


class UserRepository(BaseRepository[User]):
    """Repositorio de usuarios con consultas específicas."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, User)
        # self.db = db
        self.role_repo = RoleRepository(db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email."""
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()


    async def get_active_users(self, *, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtener usuarios activos."""
        stmt = select(User).where(User.is_active == True).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """Crea un nuevo usuario"""
        db_user = User(
            email=user_data.email, hashed_password=hashed_password, is_active=True
        )

        # Asignar roles
        if user_data.roles is not None:
            for role_name in user_data.roles:
                role = self.role_repo.get_or_create(role_name)
                db_user.roles.append(role)

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Actualiza un usuario existente"""
        db_user = await self.get(user_id)
        if not db_user:
            return None

        update_data = user_data.model_dump(exclude_unset=True, exclude={"roles"})
        for field, value in update_data.items():
            setattr(db_user, field, value)

        # Actualizar roles si se proporcionan
        if user_data.roles is not None:
            db_user.roles.clear()
            for role_name in user_data.roles:
                role = self.role_repo.get_or_create(role_name)
                db_user.roles.append(role)

        try:
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError("Error al actualizar usuario") from e


    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Obtener usuarios por rol específico"""
        return self.db.query(User).join(User.roles).filter(Role.name == role).all()

