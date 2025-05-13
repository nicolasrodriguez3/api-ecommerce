from datetime import datetime
from typing import List
from pydantic import BaseModel
from app.categories.schemas import CategoryBase


class ProductBase(BaseModel):
    name: str
    price: float
    category_id: int


class ProductCreate(ProductBase):
    description: str | None = None
    stock: int = 0


class ProductResponse(ProductCreate):
    id: int
    category: CategoryBase
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedProductResponse(BaseModel):
    data: List[ProductResponse]
    total: int
