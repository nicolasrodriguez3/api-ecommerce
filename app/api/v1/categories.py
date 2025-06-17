from fastapi import APIRouter, Depends

from app.api.dependencies import get_category_service
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get(
    "/",
    summary="Lista de categorias"
)
async def get_categories(skip: int = 0,
    limit: int = 100, category_service: CategoryService = Depends(get_category_service)):
    return await category_service.get_categories(skip=skip, limit=limit)