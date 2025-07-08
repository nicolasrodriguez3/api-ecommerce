from pydantic import Field, field_validator
from app.schemas.base import BaseResponseModel
from app.schemas.category import CategoryPublicResponse
from app.schemas.common import SortDirection


class ProductBase(BaseResponseModel):
    name: str
    price: float

    model_config = {
        "from_attributes": True,
    }


class ProductCreate(ProductBase):
    description: str | None = None
    category_id: int = 1  # Default category ID


class ProductUpdate(BaseResponseModel):
    name: str | None = None
    description: str | None = None
    category_id: int | None = None
    stock: int | None = None
    price: float | None = None
    is_active: bool | None = None


class ProductImageResponse(BaseResponseModel):
    id: int
    url: str
    position: int

    model_config = {
        "from_attributes": True,
    }


class ProductImagesResponseList(BaseResponseModel):
    images: list[ProductImageResponse]

    model_config = {
        "from_attributes": True,
    }


class UpdateProductImage(BaseResponseModel):
    position: int


class ProductPublicResponse(ProductBase):
    id: int
    description: str | None
    stock: int
    # category: CategoryPublicResponse
    category_id: int
    images: list[ProductImageResponse] = []
    is_active: bool
    is_deleted: bool
    created_at: str
    updated_at: str | None

    model_config = {
        "from_attributes": True,
    }


class PaginatedProductResponse(BaseResponseModel):
    data: list[ProductPublicResponse]
    total_elements: int
    skip: int
    limit: int
    current_page: int
    total_pages: int

    model_config = {
        "from_attributes": True,
    }


class ProductFilters(BaseResponseModel):
    """Filtros tipados para productos"""

    search: str | None = Field(None, min_length=1, max_length=100)
    min_price: float | None = Field(None, ge=0)
    max_price: float | None = Field(None, ge=0)
    category_id: int | None = None
    category_ids: list[int] | None = None
    is_active: bool = Field(True, description="Filtrar por productos activos")

    @field_validator("max_price")
    def validate_price_range(cls, v, values):
        min_price = values.get("min_price")
        if v is not None and min_price is not None and v < min_price:
            raise ValueError("max_price must be greater than or equal to min_price")
        return v


class ProductQuery(BaseResponseModel):
    """Parámetros de consulta unificados"""

    filters: ProductFilters | None = None
    order_by: str = Field("id", description="Campo por el cual ordenar")
    order_direction: SortDirection = Field(
        SortDirection.ASC, description="Dirección del ordenamiento"
    )
    include_images: bool = True
    include_category: bool = True
    include_total: bool = False