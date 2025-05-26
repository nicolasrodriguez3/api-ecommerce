from datetime import datetime
from typing import List
from pydantic import BaseModel
from app.categories.schemas import CategoryResponse


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


class ProductImageResponse(BaseModel):
    url: str
    is_main: bool

    model_config = {
        "from_attributes": True,
    }

class ProductPublicResponse(ProductBase):
    id: int
    description: str | None
    stock: int
    category: CategoryResponse
    images: List[ProductImageResponse] = []
    created_at: datetime
    updated_at: datetime


class PaginatedProductResponse(BaseModel):
    data: List[ProductPublicResponse]
    page: int
    total_pages: int


class StockUpdate(BaseModel):
    stock: int


class StockAdjustment(BaseModel):
    quantity: int


class StockHistoryResponse(BaseModel):
    id: int
    quantity: int
    reason: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "extra": "ignore",
    }
