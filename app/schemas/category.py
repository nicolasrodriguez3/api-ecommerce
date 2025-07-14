from pydantic import Field, field_validator

from app.enums.category import CategoryOrderField
from app.enums.order_direction import OrderDirection
from app.schemas.base import BaseResponseModel
from app.schemas.common import PaginationParams, PaginationRequest


class CategoryBase(BaseResponseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Nombre de la categoría"
    )

    model_config = {
        "from_attributes": True,
        "extra": "ignore",
    }


class CategoryCreate(CategoryBase):
    """Esquema para crear una nueva categoría."""

    pass


class CategoryUpdate(BaseResponseModel):
    """Esquema para actualizar una categoría."""

    name: str | None = Field(
        None, min_length=1, max_length=100, description="Nombre de la categoría"
    )


class CategoryPublicResponse(CategoryBase):
    """Esquema de respuesta pública de categoría."""

    id: int
    created_at: str
    updated_at: str | None = None
    product_count: int = Field(0, description="Número de productos en la categoría")
    is_deleted: bool = False

    model_config = {
        "from_attributes": True,
    }


class CategoryWithProductCount(CategoryPublicResponse):
    """Esquema de categoría con conteo de productos."""

    active_product_count: int = Field(
        ..., description="Número de productos activos en la categoría"
    )


class CategoryInProduct(BaseResponseModel):
    """Esquema de categoría para incluir en productos."""

    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class CategoryFilters(BaseResponseModel):
    """DTO para filtros de categorías"""

    search: str | None = Field(None, description="Buscar por nombre de categoría")
    order_by: CategoryOrderField = Field(
        CategoryOrderField.ID, description="Campo de ordenamiento"
    )
    order_dir: OrderDirection = Field(
        OrderDirection.ASC, description="Dirección del orden"
    )
    include_product_count: bool = Field(
        False, description="Incluir conteo de productos por categoría"
    )
    include_deleted: bool = Field(False, description="Incluir categorías eliminadas")

    @field_validator("search")
    def validate_search(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError(
                    "El término de búsqueda debe tener al menos 2 caracteres"
                )
        return v
    
class CategoryQuery(BaseResponseModel):
    """DTO unificado para consultas de categorías"""
    pagination: PaginationParams
    filters: CategoryFilters

    @classmethod
    def from_request(cls, pagination_request: PaginationRequest, filters: CategoryFilters) -> 'CategoryQuery':
        return cls(
            pagination=PaginationParams.from_request(pagination_request),
            filters=filters
        )
