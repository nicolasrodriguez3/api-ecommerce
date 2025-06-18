from fastapi import APIRouter, Depends

from app.api.dependencies import get_category_service
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    PaginatedCategoryResponse,
)
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", summary="Lista de categorias")
async def get_categories(
    skip: int = 0,
    limit: int = 100,
    category_service: CategoryService = Depends(get_category_service),
) -> PaginatedCategoryResponse:
    return await category_service.get_categories(skip=skip, limit=limit)


@router.get(
    "/{category_id}",
)
async def get_category_by_id(
    category_id: int, category_service: CategoryService = Depends(get_category_service)
) -> CategoryResponse:
    return await category_service.get_by_id(category_id)


@router.post(
    "/",
)
async def create_category(
    category_data: CategoryCreate,
    category_service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    return await category_service.create_category(category_data)
