from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)
from datetime import datetime
from .base_model import BaseModel


class UserModel(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="customer")
    created_at = Column(DateTime, default=datetime.now())
