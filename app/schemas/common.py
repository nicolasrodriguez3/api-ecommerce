from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")

class PaginatedResponse(GenericModel, Generic[T]):    
    data: list[T]
    total_elements: int
    current_page: int
    total_pages: int