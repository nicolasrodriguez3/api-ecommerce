from sqlalchemy import select
from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repositorio de productos con consultas específicas."""

    def __init__(self, db):
        super().__init__(db, Product)

    async def get_by_name(self, name: str) -> Product | None:
        """Obtener producto por nombre."""
        stmt = select(Product).where(Product.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    async def get_active_products(self, *, skip: int = 0, limit: int = 100) -> list[Product]:
        """Obtener productos activos."""
        stmt = select(Product).where(Product.is_active == True).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())