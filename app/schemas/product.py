from datetime import datetime
from typing import List
from pydantic import BaseModel
from app.categories.schemas import CategoryResponse


# Products
class ProductBase(BaseModel):
    name: str
    price: float

    model_config = {
        "from_attributes": True,
        "extra": "ignore",
    }


class ProductCreate(ProductBase):
    description: str | None = None
    category_id: int = 1  # Default category ID


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category_id: int | None = None
    stock: int | None = None
    price: float | None = None



class ProductImageResponse(BaseModel):
    id: int
    url: str
    position: int

    model_config = {
        "from_attributes": True,
    }


class ProductPublicResponse(ProductBase):
    id: int
    description: str | None
    stock: int
    # category: CategoryResponse
    category_id: int
    images: List[ProductImageResponse] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "extra": "ignore",
    }


class PaginatedProductResponse(BaseModel):
    data: List[ProductPublicResponse]
    total_elements: int
    skip: int
    limit: int

