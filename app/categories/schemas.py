from typing import List
from pydantic import BaseModel
from datetime import datetime


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedCategoryResponse(BaseModel):
    data: List[CategoryResponse]
    total: int
