from typing import List
from pydantic import BaseModel

from app.schemas.base import BaseResponseModel


class CategoryBase(BaseResponseModel):
    name: str

    model_config = {
        "from_attributes": True,
        "extra": "ignore",
    }


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    created_at: str
    updated_at: str | None


class PaginatedCategoryResponse(BaseModel):
    data: List[CategoryResponse]
    total_elements: int
    skip: int
    limit: int
