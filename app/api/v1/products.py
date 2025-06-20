from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies import get_product_service
from app.auth.dependencies import get_current_user, require_admin
from app.schemas.product import PaginatedProductResponse, ProductCreate, ProductImageResponse, ProductImagesResponseList, ProductPublicResponse, ProductUpdate, UpdateProductImage
from app.services.product import ProductService


router = APIRouter(prefix="/products", tags=["products"])


@router.get(
    "/",
    summary="Listar productos",
    description="Obtiene una lista paginada de productos",
)
async def get_products(
    skip: int = 0,
    limit: int = 100,
    product_service: ProductService = Depends(get_product_service)
) -> PaginatedProductResponse:
    """Obtener lista de productos."""
    return await product_service.get_products(skip=skip, limit=limit)


@router.get(
    "/{product_id}",
    summary="Obtener producto",
    description="Obtiene un producto por su ID",
)
async def get_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service)
) -> ProductPublicResponse:
    """Obtener producto por ID."""
    return await product_service.get_product_by_id(product_id)


@router.post(
    "/",
    summary="Crear producto",
    description="Crea un nuevo producto",
    dependencies=[Depends(get_current_user), Depends(require_admin)]
)
async def create_product(
    product_data: ProductCreate,
    product_service: ProductService = Depends(get_product_service)
) -> ProductPublicResponse:
    """Crear un nuevo producto."""
    return await product_service.create_product(product_data)


@router.put(
    "/{product_id}",
    summary="Actualizar un producto",
    dependencies=[Depends(get_current_user), Depends(require_admin)]
)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    product_service: ProductService = Depends(get_product_service)
) -> ProductPublicResponse:
    return await product_service.update_product(product_id, product_data)


# Images
@router.post("/{product_id}/images", status_code=201)
async def upload_image(
    product_id: int,
    file: UploadFile = File(...),
    product_service: ProductService = Depends(get_product_service)
) -> ProductImageResponse:
    return await product_service.upload_image(product_id, file)


@router.get("/{product_id}/images")
async def get_images(
    product_id: int,
    product_service: ProductService = Depends(get_product_service)
) -> ProductImagesResponseList:
    return await product_service.get_product_images(product_id)


@router.delete("/{product_id}/images/{image_id}", status_code=204)
async def delete_image(
    product_id: int,
    image_id: int,
    product_service: ProductService = Depends(get_product_service)
) -> None:
    return await product_service.delete_image(product_id, image_id)


@router.put("/{product_id}/images/{image_id}/position")
async def update_image_position(
    product_id: int,
    image_id: int,
    position_data: UpdateProductImage,
    product_service: ProductService = Depends(get_product_service)
) -> ProductImageResponse:
    return await product_service.update_image_position(
        image_id=image_id,
        new_position=position_data.position,
        product_id=product_id
    )