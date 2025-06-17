from fastapi import APIRouter, Depends

from app.api.dependencies import get_product_service
from app.auth.dependencies import get_current_user, require_admin
from app.schemas.product import PaginatedProductResponse, ProductCreate, ProductPublicResponse, ProductUpdate
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