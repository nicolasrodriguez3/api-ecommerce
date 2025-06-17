from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.product import ProductService
from app.services.user import UserService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependencia para obtener servicio de usuarios."""
    return UserService(db)

def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    """Dependencia para obtener servicio de productos."""
    from app.services.product import ProductService
    return ProductService(db)