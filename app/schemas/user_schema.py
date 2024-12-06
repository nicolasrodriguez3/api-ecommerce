from pydantic import BaseModel, EmailStr
from datetime import datetime

# Schema para crear un usuario (entrada)
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

# Schema para leer un usuario (salida)
class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
