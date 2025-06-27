from app.schemas.base import BaseResponseModel


# Products
class ProductBase(BaseResponseModel):
    name: str
    price: float

    model_config = {
        "from_attributes": True,
        "extra": "ignore",
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
    # category: CategoryResponse
    category_id: int
    images: list[ProductImageResponse] = []
    created_at: str
    updated_at: str | None

    model_config = {
        "from_attributes": True,
        "extra": "ignore",
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
