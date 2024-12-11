from sqlalchemy import Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base_model import BaseModel


class ProductModel(BaseModel):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name = mapped_column(String, nullable=False)
    description = mapped_column(String, nullable=False)
    price = mapped_column(Float, nullable=False)
    stock = mapped_column(Integer, nullable=False)
    category_id = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    image_url = mapped_column(String)
    created_at = mapped_column(DateTime, default=datetime.now())
    updated_at = mapped_column(
        DateTime, default=datetime.now(), onupdate=datetime.now()
    )


class CategoryModel(BaseModel):
    __tablename__ = "categories"

    id = mapped_column(Integer, primary_key=True, index=True)
    name = mapped_column(String, nullable=False)
    created_at = mapped_column(DateTime, default=datetime.now())
