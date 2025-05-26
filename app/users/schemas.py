from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    role: str

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None
