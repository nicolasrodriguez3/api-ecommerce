from datetime import datetime
from typing import List
from pydantic import BaseModel
from app.categories.schemas import CategoryBase


class ProductBase(BaseModel):
    name: str
    price: float
    
    model_config = {
        "from_attributes": True,
        "extra": "ignore",
    }


class ProductCreate(ProductBase):
    description: str | None = None
    category_id: int
    stock: int = 0


class ProductResponse(ProductBase):
    id: int
    description: str | None
    stock: int
    category: CategoryBase
    created_at: datetime
    updated_at: datetime


class PaginatedProductResponse(BaseModel):
    data: List[ProductResponse]
    total: int
