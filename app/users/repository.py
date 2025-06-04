from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.users.models import Role, User, UserRole
from app.users.schemas import UserCreate, UserUpdate
from sqlalchemy.exc import IntegrityError


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


class UserRepository:
    """Repositorio de usuarios con consultas específicas."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.role_repo = RoleRepository(db)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene usuario por ID"""
        stmt = select(User).where(User.id == user_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email."""
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    async def get_users(self, *, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtener usuarios."""
        stmt = select(User).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    async def get_active_users(self, *, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtener usuarios activos."""
        stmt = select(User).where(User.is_active == True).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    async def create(self, user_data: UserCreate, hashed_password: str) -> User:
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

    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Actualiza un usuario existente"""
        db_user = await self.get_by_id(user_id)
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

    async def delete(self, user_id: int) -> bool:
        db_user = await self.get_by_id(user_id)
        if not db_user:
            return False

        self.db.delete(db_user)
        self.db.commit()
        return True

    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Obtener usuarios por rol específico"""
        return self.db.query(User).join(User.roles).filter(Role.name == role).all()

    async def exists(self, user_id: int) -> bool:
        """Verifica si un usuario existe por ID"""
        stmt = select(func.count(User.id)).where(User.id == user_id)
        result = self.db.execute(stmt).scalar()
        return result > 0 if result is not None else False
