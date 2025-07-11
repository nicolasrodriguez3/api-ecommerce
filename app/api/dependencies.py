from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.services.category import CategoryService
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
