from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.models.user import UserRole
from app.schemas.base import BaseResponseModel


class RoleBase(BaseResponseModel):
    name: UserRole
    description: str | None = None


class RoleResponse(RoleBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBase(BaseResponseModel):
    email: EmailStr


class NewUserCreate(UserBase):
    password: str


class UserCreate(UserBase):
    roles: Optional[List[UserRole]] = Field(default_factory=lambda: [UserRole.CUSTOMER])
    password: str
    is_active: bool = True

    model_config = {
        "use_enum_values": True,
    }


class UserInDB(UserBase):
    id: int
    hashed_password: str
    created_at: str
    updated_at: str | None = None
    roles: List[UserRole] = Field(default_factory=list)
    
    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: str
    roles: List[str] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }

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
