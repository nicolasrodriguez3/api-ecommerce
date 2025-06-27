from typing import List
from pydantic import Field

from app.schemas.base import BaseResponseModel


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
    product_count: int = Field(
        0, description="Número de productos en la categoría"
    )
    is_deleted: bool = False

    model_config = {
        "from_attributes": True,
    }


class CategoryWithProductCount(CategoryPublicResponse):
    """Esquema de categoría con conteo de productos."""

    active_product_count: int = Field(
        ..., description="Número de productos activos en la categoría"
    )


class PaginatedCategoryResponse(BaseResponseModel):
    """Esquema de respuesta paginada para categorías."""

    data: list[CategoryPublicResponse]
    total_elements: int = Field(..., description="Total de elementos en la consulta")
    skip: int = Field(..., description="Número de elementos saltados")
    limit: int = Field(..., description="Límite de elementos por página")
    current_page: int = Field(..., description="Página actual")
    total_pages: int = Field(..., description="Total de páginas")


class CategoryInProduct(BaseResponseModel):
    """Esquema de categoría para incluir en productos."""
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }
