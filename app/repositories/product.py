from sqlalchemy import select
from app.models.product import Product
from app.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

class ProductRepository(BaseRepository[Product]):
    """Repositorio de productos con consultas específicas."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Product)

    async def get_by_name(self, name: str) -> Product | None:
        """Obtener producto por nombre."""
        stmt = select(Product).where(Product.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_products(self, *, skip: int = 0, limit: int = 100) -> list[Product]:
        """Obtener productos activos."""
        stmt = select(Product).where(Product.is_active == True).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())