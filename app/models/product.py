from typing import List
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.models.base import BaseModel
from app.models.category import Category


class Product(BaseModel):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(default=0)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped[Category] = relationship("Category", back_populates="products")

    # order_items: Mapped[list["OrderItem"]] = relationship(
    #     "OrderItem", back_populates="product"
    # )


# class ProductImage(Base):
#     __tablename__ = "product_images"

#     id: Mapped[int] = mapped_column(primary_key=True, index=True)
#     product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
#     url: Mapped[str] = mapped_column(String, nullable=False)
#     public_id: Mapped[str] = mapped_column(String, nullable=False)
#     position: Mapped[int] = mapped_column(default=0)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

#     product: Mapped[Product] = relationship("Product", back_populates="images")
