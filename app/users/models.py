from typing import List
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.auth.models import RefreshToken
from app.core.database import Base
from app.customers.models import Customer
from app.orders.models import Order
from app.users.roles import RoleEnum


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default=RoleEnum.CUSTOMER.value
    )

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    customer: Mapped[Customer] = relationship("Customer", uselist=False, back_populates="user")

    refresh_tokens: Mapped[List[RefreshToken]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")
