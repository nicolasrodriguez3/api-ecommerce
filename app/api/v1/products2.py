from typing import Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.api.dependencies import get_product_service2
from app.auth.dependencies import get_current_user, require_admin
from app.schemas.common import PaginatedResponse, PaginationParams, ProductFilters, ProductQuery, SortDirection
from app.schemas.product import (
    PaginatedProductResponse,
    ProductCreate,
    ProductImageResponse,
    ProductImagesResponseList,
    ProductPublicResponse,
    ProductUpdate,
    UpdateProductImage,
)
from app.services.product import ProductService


router = APIRouter(prefix="/products2", tags=["products2"])

@router.get("/products", response_model=PaginatedResponse[ProductResponse])
async def get_products(
    # Parámetros de paginación
    cursor: Optional[str] = Query(None, description="Cursor para paginación"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados"),
    direction: str = Query("next", regex="^(next|prev)$"),
    
    # Parámetros de filtrado
    search: Optional[str] = Query(None, description="Búsqueda por nombre/descripción"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    min_price: Optional[float] = Query(None, ge=0, description="Precio mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Precio máximo"),
    
    # Parámetros de ordenamiento
    order_by: str = Query("id", description="Campo de ordenamiento"),
    order_direction: SortDirection = Query(SortDirection.ASC, description="Dirección"),
    
    # Parámetros de carga
    include_images: bool = Query(True, description="Incluir imágenes"),
    include_category: bool = Query(True, description="Incluir categoría"),
    include_total: bool = Query(False, description="Incluir conteo total"),
    
    # Service
    product_service = Depends(get_product_service2)
):
    """
    Obtener productos con paginación cursor-based optimizada
    
    ✅ Ventajas sobre el endpoint anterior:
    - Paginación O(1) en lugar de O(n)
    - Carga de relaciones configurable
    - Conteo total opcional (para mejor rendimiento)
    - Filtros tipados y validados
    - Cursor estable para tiempo real
    """
    
    # Crear parámetros de paginación
    pagination = PaginationParams(
        cursor=cursor,
        limit=limit,
        direction=direction
    )
    
    # Crear filtros
    filters = ProductFilters(
        search=search,
        is_active=is_active,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price
    )
    
    # Crear query params
    query_params = ProductQuery(
        filters=filters,
        order_by=order_by,
        order_direction=order_direction,
        include_images=include_images,
        include_category=include_category
    )
    
    # Ejecutar búsqueda
    result = await repo.search_products(query_params, pagination)
    
    # Si se solicita total, agregarlo
    if include_total and isinstance(result, PaginatedResponse):
        result.total_count = await repo.get_approximate_count(filters)
    
    return result


@router.get(
    "/{product_id}",
    summary="Obtener producto",
    description="Obtiene un producto por su ID",
)
async def get_product(
    product_id: int, product_service: ProductService = Depends(get_product_service)
) -> ProductPublicResponse:
    """Obtener producto por ID."""
    return await product_service.get_product_by_id(product_id)


@router.post(
    "/",
    summary="Crear producto",
    description="Crea un nuevo producto",
    dependencies=[Depends(get_current_user), Depends(require_admin)],
)
async def create_product(
    product_data: ProductCreate,
    product_service: ProductService = Depends(get_product_service),
) -> ProductPublicResponse:
    """Crear un nuevo producto."""
    return await product_service.create_product(product_data)


@router.put(
    "/{product_id}",
    summary="Actualizar un producto",
    dependencies=[Depends(get_current_user), Depends(require_admin)],
)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    product_service: ProductService = Depends(get_product_service),
) -> ProductPublicResponse:
    return await product_service.update_product(product_id, product_data)

@router.delete(
    "/{product_id}",
    summary="Eliminar producto",
    description="Elimina un producto del sistema (soft delete).",
    status_code=204
)
async def delete_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service),
    current_user = Depends(require_admin),  # Solo administradores pueden eliminar productos
):
    """Eliminar producto (soft delete)."""
    return await product_service.delete_product(product_id)

# Images
@router.post("/{product_id}/images", status_code=201)
async def upload_image(
    product_id: int,
    file: UploadFile = File(...),
    product_service: ProductService = Depends(get_product_service),
) -> ProductImageResponse:
    return await product_service.upload_image(product_id, file)


@router.get("/{product_id}/images")
async def get_images(
    product_id: int, product_service: ProductService = Depends(get_product_service)
) -> ProductImagesResponseList:
    return await product_service.get_product_images(product_id)


@router.delete("/{product_id}/images/{image_id}", status_code=204)
async def delete_image(
    product_id: int,
    image_id: int,
    product_service: ProductService = Depends(get_product_service),
) -> None:
    return await product_service.delete_image(product_id, image_id)


@router.put("/{product_id}/images/{image_id}/position")
async def update_image_position(
    product_id: int,
    image_id: int,
    position_data: UpdateProductImage,
    product_service: ProductService = Depends(get_product_service),
) -> ProductImageResponse:
    return await product_service.update_image_position(
        image_id=image_id, new_position=position_data.position, product_id=product_id
    )
