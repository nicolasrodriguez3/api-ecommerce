from app.schemas.base import BaseResponseModel
from app.schemas.category import CategoryPublicResponse


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


