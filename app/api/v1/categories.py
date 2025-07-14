from fastapi import APIRouter, Depends, Query

from app.api.dependencies import (
    get_category_filters,
    get_category_service,
    get_pagination_params,
)
from app.auth.dependencies import require_admin
from app.schemas.category import (
    CategoryCreate,
    CategoryFilters,
    CategoryPublicResponse,
    CategoryPublicResponse,
    CategoryQuery,
    CategoryUpdate,
)
from app.schemas.common import PaginatedResponse, PaginationRequest
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "/",
    summary="Listar categorías",
    description="Obtiene una lista paginada de categorías con filtros opcionales",
    response_model=PaginatedResponse[CategoryPublicResponse],
)
async def get_categories(
    pagination: PaginationRequest = Depends(get_pagination_params),
    filters: CategoryFilters = Depends(get_category_filters),
    category_service: CategoryService = Depends(get_category_service),
) -> PaginatedResponse[CategoryPublicResponse]:
    """Obtener lista de categorías con filtros opcionales."""
    query = CategoryQuery.from_request(pagination, filters)
    return await category_service.get_categories(query)


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
    current_user=Depends(require_admin),  # Solo administradores pueden crear categorías
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
    current_user=Depends(
        require_admin
    ),  # Solo administradores pueden actualizar categorías
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
    current_user=Depends(
        require_admin
    ),  # Solo administradores pueden eliminar categorías
) -> dict[str, str | int]:
    """Eliminar categoría (soft delete)."""
    return await category_service.delete_category(category_id)
