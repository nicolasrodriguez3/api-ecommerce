from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.services.category import CategoryService
from app.services.order import OrderService
from app.services.product import ProductService
from app.services.user import UserService


def get_user_service(db: AsyncSession = Depends(get_session)) -> UserService:
    """Dependencia para obtener servicio de usuarios."""
    return UserService(db)


def get_product_service(db: AsyncSession = Depends(get_session)) -> ProductService:
    """Dependencia para obtener servicio de productos."""
    return ProductService(db)


def get_category_service(db: AsyncSession = Depends(get_session)) -> CategoryService:
    """Dependencia para obtener servicio de productos."""
    return CategoryService(db)

# Dependency para obtener el servicio de órdenes
async def get_order_service(
    db: AsyncSession = Depends(get_session),
    # inventory_service: InventoryService = Depends(),
    # notification_service: NotificationService = Depends()
) -> OrderService:
    return OrderService(db)