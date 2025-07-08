from math import ceil
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, field_validator
from pydantic.generics import GenericModel

T = TypeVar("T")

from typing import Any, Dict, List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from enum import Enum

T = TypeVar("T")


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    """Parámetros de paginación mejorados"""

    cursor: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    direction: str = Field(default="next", pattern="^(next|prev)$")


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica"""

    items: List[T]
    has_next: bool
    has_prev: bool
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    total_count: Optional[int] = None


