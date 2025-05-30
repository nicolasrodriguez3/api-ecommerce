from typing import List
from app.core.database import Base
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    total_amount: Mapped[float] = mapped_column(nullable=False)
    observations: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    sync_statuses: Mapped[List["SyncStatus"]] = relationship("SyncStatus", back_populates="order", cascade="all, delete-orphan")
    user: Mapped["User"] = relationship("User", back_populates="orders")  # type: ignore
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[float] = mapped_column(nullable=False)
    total_price: Mapped[float] = mapped_column(nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")  # type: ignore
    


class SyncStatus(Base):
    __tablename__ = "sync_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # ej: 'cianbox'
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # 'pending', 'synced', 'error'
    synced_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="sync_statuses")
