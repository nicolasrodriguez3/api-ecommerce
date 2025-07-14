from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.enums.category import CategoryOrderField
from app.enums.order_direction import OrderDirection
from app.schemas.category import CategoryFilters
from app.schemas.common import PaginationRequest
from app.services.category import CategoryService
from app.services.product import ProductService
from app.services.user import UserService


def get_pagination_params(
    page: int = 1,
    per_page: int = 10,
) -> PaginationRequest:
    return PaginationRequest(
        page=page,
        per_page=per_page,
    )


def get_user_service(db: AsyncSession = Depends(get_session)) -> UserService:
    """Dependencia para obtener servicio de usuarios."""
    return UserService(db)


def get_product_service(db: AsyncSession = Depends(get_session)) -> ProductService:
    """Dependencia para obtener servicio de productos."""
    return ProductService(db)


# CATEGORIES
def get_category_service(db: AsyncSession = Depends(get_session)) -> CategoryService:
    """Dependencia para obtener servicio de productos."""
    return CategoryService(db)


def get_category_filters(
    search: str | None = Query(None, description="Buscar por nombre de categoría"),
    order_by: CategoryOrderField = Query(
        CategoryOrderField.ID, description="Campo de ordenamiento"
    ),
    order_dir: OrderDirection = Query(
        OrderDirection.ASC, description="Dirección del orden"
    ),
    include_product_count: bool = Query(
        False, description="Incluir conteo de productos por categoría"
    ),
    include_deleted: bool = Query(False, description="Incluir categorías eliminadas"),
) -> CategoryFilters:
    return CategoryFilters(
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        include_product_count=include_product_count,
        include_deleted=include_deleted,
    )
