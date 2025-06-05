from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.models.user import UserRole


class RoleBase(BaseModel):
    name: UserRole
    description: str | None = None


class RoleResponse(RoleBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBase(BaseModel):
    email: EmailStr


class NewUserCreate(UserBase):
    password: str

class UserCreate(UserBase):
    roles: Optional[List[UserRole]] = [UserRole.CUSTOMER]  # Rol por defecto
    password: str


class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    roles: List[RoleResponse] = []

    model_config = {"from_attributes": True}


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    roles: List[str] = []  # Lista de nombres de roles

    model_config = {"from_attributes": True}

    @classmethod
    def from_user(cls, user):
        """Método personalizado para crear UserResponse desde User model"""
        return cls(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            roles=user.get_role_names(),
        )


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None
    roles: Optional[List[UserRole]] = None
