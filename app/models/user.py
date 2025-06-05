import enum
from typing import List
from sqlalchemy import Enum, ForeignKey, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.core.database import Base
from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """Enumeration for user roles in the application."""

    ADMIN = "admin"
    OWNER = "owner"
    SELLER = "seller"
    CUSTOMER = "customer"


# Tabla de asociación para roles múltiples (many-to-many)
user_roles: Table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)


class Role(BaseModel):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(Enum(UserRole), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

    # Relación con usuarios
    users: Mapped[List["User"]] = relationship(
        "User", secondary=user_roles, back_populates="roles"
    )


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    # customer: Mapped[Customer] = relationship(
    #     "Customer", uselist=False, back_populates="user"
    # )

    # orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")

    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary=user_roles, back_populates="users"
    )

    def has_role(self, role: UserRole) -> bool:
        """Verificar si el usuario tiene un rol específico"""
        return any(r.name == role for r in self.roles)

    def has_any_role(self, roles: list[UserRole]) -> bool:
        """Verificar si el usuario tiene alguno de los roles especificados"""
        return any(self.has_role(role) for role in roles)

    def get_role_names(self) -> list[str]:
        """Obtener lista de nombres de roles del usuario"""
        return [role.name for role in self.roles]
