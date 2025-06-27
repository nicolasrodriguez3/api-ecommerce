from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_category_service
from app.auth.dependencies import require_admin
from app.schemas.category import (
    CategoryCreate,
    CategoryPublicResponse,
    CategoryPublicResponse,
    CategoryUpdate,
    PaginatedCategoryResponse,
)
from app.schemas.product import PaginatedProductResponse
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "/",
    summary="Listar categorías",
    description="Obtiene una lista paginada de categorías con filtros opcionales",
    response_model=PaginatedCategoryResponse,
)
async def get_categories(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(
        10, ge=1, le=100, description="Máximo número de categorías a devolver"
    ),
    search: str | None = Query(None, description="Buscar por nombre de categoría"),
    order_by: str = Query(
        "id", description="Campo de ordenamiento (id, name, created_at, updated_at)"
    ),
    order_dir: str = Query(
        "asc", pattern="^(asc|desc)$", description="Dirección del orden"
    ),
    include_product_count: bool = Query(
        False, description="Incluir conteo de productos por categoría"
    ),
    include_deleted: bool = Query(
        False, description="Incluir categorias eliminadas"
    ),
    category_service: CategoryService = Depends(get_category_service),
) -> PaginatedCategoryResponse:
    """Obtener lista de categorías con filtros opcionales."""
    return await category_service.get_categories(
        skip=skip,
        limit=limit,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        include_product_count=include_product_count,
        include_deleted=include_deleted,
    )

@router.get(
    "/{category_id}",
    summary="Obtener categoría por ID",
    description="Obtiene los detalles de una categoría específica",
    response_model=CategoryPublicResponse,
)
async def get_category(
    category_id: int,
    category_service: CategoryService = Depends(get_category_service),
) -> CategoryPublicResponse:
    """Obtener categoría por ID."""
    return await category_service.get_category_by_id(category_id)


@router.post(
    "/",
    summary="Crear nueva categoría",
    description="Crea una nueva categoría en el sistema",
    response_model=CategoryPublicResponse,
    status_code=201,
)
async def create_category(
    category_data: CategoryCreate,
    category_service: CategoryService = Depends(get_category_service),
    current_user = Depends(require_admin),  # Solo administradores pueden crear categorías
) -> CategoryPublicResponse:
    """Crear nueva categoría."""
    return await category_service.create_category(category_data)


@router.put(
    "/{category_id}",
    summary="Actualizar categoría",
    description="Actualiza los datos de una categoría existente",
    response_model=CategoryPublicResponse,
)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    category_service: CategoryService = Depends(get_category_service),
    current_user = Depends(require_admin),  # Solo administradores pueden actualizar categorías
) -> CategoryPublicResponse:
    """Actualizar categoría existente."""
    return await category_service.update_category(category_id, category_data)


@router.delete(
    "/{category_id}",
    summary="Eliminar categoría",
    description="Elimina una categoría del sistema (soft delete). No se puede eliminar si tiene productos activos.",
    response_model=dict[str, str | int],
)
async def delete_category(
    category_id: int,
    category_service: CategoryService = Depends(get_category_service),
    current_user = Depends(require_admin),  # Solo administradores pueden eliminar categorías
) -> dict[str, str | int]:
    """Eliminar categoría (soft delete)."""
    return await category_service.delete_category(category_id)


@router.get(
    "/{category_id}/products",
    summary="Obtener productos de una categoría",
    description="Obtiene una lista paginada de productos que pertenecen a una categoría específica",
    response_model=PaginatedProductResponse,
)
async def get_category_products(
    category_id: int,
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo número de productos a devolver"),
    is_active: bool = Query(True, description="Filtrar solo productos activos"),
    category_service: CategoryService = Depends(get_category_service),
) -> PaginatedProductResponse:
    """Obtener productos de una categoría específica."""
    return await category_service.get_category_products(
        category_id=category_id,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )