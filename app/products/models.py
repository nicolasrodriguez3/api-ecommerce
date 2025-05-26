from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Float, ForeignKey, Boolean
from datetime import datetime
from app.core.database import Base
from app.stock.models import StockHistory


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(default=0)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False
    )
    images: Mapped[List["ProductImage"]] = relationship(
        "ProductImage", back_populates="product", cascade="all, delete-orphan"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped["Category"] = relationship("Category", back_populates="products")  # type: ignore
    stock_history: Mapped[List["StockHistory"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    product: Mapped[Product] = relationship("Product", back_populates="images")
