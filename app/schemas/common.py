from pydantic import BaseModel
from typing import Generic, List, TypeVar

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total_elements: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

    model_config = {
        "from_attributes": True,
    }
