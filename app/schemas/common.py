import math
from pydantic import BaseModel, Field, computed_field
from typing import Generic, List, TypeVar

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total_elements: int
    page: int
    per_page: int

    @computed_field
    @property
    def total_pages(self) -> int:
        return (
            math.ceil(self.total_elements / self.per_page)
            if self.total_elements > 0
            else 1
        )

    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @computed_field
    @property
    def has_previous(self) -> bool:
        return self.page > 1

    @computed_field
    @property
    def next_page(self) -> int | None:
        return self.page + 1 if self.has_next else None

    @computed_field
    @property
    def previous_page(self) -> int | None:
        return self.page - 1 if self.has_previous else None

    model_config = {
        "from_attributes": True,
    }


class PaginationRequest(BaseModel):
    page: int = Field(1, ge=1, description="Número de página")
    per_page: int = Field(10, ge=1, le=1000, description="Límite de registros")
    # order_by: str = Field("id", description="Campo por el cual ordenar los resultados")
    # order_dir: str = Field("asc", description="Dirección del orden ('asc' o 'desc')")


class PaginationParams(BaseModel):
    """DTO para capas de negocio/repositorio"""

    limit: int = Field(ge=1)
    offset: int = Field(ge=0)

    @classmethod
    def from_request(cls, request: PaginationRequest) -> "PaginationParams":
        return cls(limit=request.per_page, offset=(request.page - 1) * request.per_page)

    @computed_field
    @property
    def page(self) -> int:
        return math.ceil(self.offset / self.limit) + 1

    @computed_field
    @property
    def per_page(self) -> int:
        return self.limit



        