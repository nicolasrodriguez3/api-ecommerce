from typing import Any, Dict, List
from sqlalchemy import select, func, desc, asc, and_, or_, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.category import Category
from app.models.product import Product
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repositorio de categorías con consultas específicas."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Category)

    async def get_by_name(self, name: str) -> Category | None:
        """Obtener categoría por nombre."""
        stmt = select(Category).where(
            and_(Category.name == name, Category.is_deleted == False)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_categories_with_filters(
        self,
        skip: int = 0,
        limit: int = 10,
        filters: Dict[str, Any] | None = None,
        order_by: str = "id",
        order_dir: str = "asc",
        include_product_count: bool = False,
        include_deleted: bool = False,
    ) -> List[Category]:
        """Obtener categorías con filtros aplicados."""
        if filters is None:
            filters = {}

        # Construir query base
        stmt = select(Category)
        if not include_deleted:
            stmt = stmt.where(Category.is_deleted == False)

        # Aplicar filtros
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            stmt = stmt.where(Category.name.ilike(search_term))

        # Si necesitamos el conteo de productos, hacer join
        if include_product_count:
            stmt = stmt.options(selectinload(Category.products))

        # Aplicar ordenamiento
        order_column = getattr(Category, order_by)
        if order_dir == "desc":
            stmt = stmt.order_by(desc(order_column))
        else:
            stmt = stmt.order_by(asc(order_column))

        # Aplicar paginación
        stmt = stmt.offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_categories_with_filters(
        self,
        filters: Dict[str, Any] | None = None,
        include_deleted=False,
    ) -> int:
        """Contar categorías con filtros aplicados."""
        if filters is None:
            filters = {}

        # Construir query de conteo
        stmt = select(func.count(Category.id))
        if not include_deleted:
            stmt = stmt.where(Category.is_deleted == False)

        # Aplicar filtros
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            stmt = stmt.where(Category.name.ilike(search_term))

        result = await self.db.execute(stmt)
        count = result.scalar()
        return count if count is not None else 0

    async def get_category_products(
        self,
        category_id: int,
        skip: int = 0,
        limit: int = 10,
        is_active: bool = True,
    ) -> List[Product]:
        """Obtener productos de una categoría específica."""
        stmt = (
            select(Product)
            .where(Product.category_id == category_id)
            .where(Product.is_deleted == False)
        )

        if is_active:
            stmt = stmt.where(Product.is_active == True)

        # Ordenar por ID por defecto
        stmt = stmt.order_by(asc(Product.id))

        # Aplicar paginación
        stmt = stmt.offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_products_in_category(
        self, category_id: int, is_active: bool = True
    ) -> int:
        """Contar productos en una categoría."""
        stmt = (
            select(func.count(Product.id))
            .where(Product.category_id == category_id)
            .where(Product.is_deleted == False)
        )

        if is_active:
            stmt = stmt.where(Product.is_active == True)

        result = await self.db.execute(stmt)
        count = result.scalar()
        return count if count is not None else 0

    async def count_active_products_in_category(self, category_id: int) -> int:
        """Contar productos activos en una categoría (para validación antes de eliminar)."""
        return await self.count_products_in_category(category_id, is_active=True)

    async def category_soft_delete(self, category_id: int) -> bool:
        """Realizar soft delete de una categoría."""
        stmt = (
            sql_update(Category)
            .where(Category.id == category_id)
            .values(is_deleted=True, updated_at=func.now())
        )
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    async def get_by_id(self, obj_id: int) -> Category | None:
        """Override para incluir filtro de soft delete."""
        stmt = select(Category).where(Category.id == obj_id)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_categories_with_product_counts(
        self,
        skip: int = 0,
        limit: int = 10,
        filters: Dict[str, Any] | None = None,
        order_by: str = "id",
        order_dir: str = "asc",
    ) -> List[Dict[str, Any]]:
        """Obtener categorías con conteo de productos."""
        if filters is None:
            filters = {}

        # Query con LEFT JOIN para obtener conteo de productos
        stmt = (
            select(
                Category.id,
                Category.name,
                Category.created_at,
                Category.updated_at,
                func.count(Product.id).label("product_count"),
            )
            .outerjoin(
                Product,
                and_(
                    Product.category_id == Category.id,
                    Product.is_deleted == False,
                    Product.is_active == True,
                ),
            )
            .where(Category.is_deleted == False)
            .group_by(Category.id)
        )

        # Aplicar filtros
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            stmt = stmt.where(Category.name.ilike(search_term))

        # Aplicar ordenamiento
        if order_by == "product_count":
            order_column = func.count(Product.id)
        else:
            order_column = getattr(Category, order_by)

        if order_dir == "desc":
            stmt = stmt.order_by(desc(order_column))
        else:
            stmt = stmt.order_by(asc(order_column))

        # Aplicar paginación
        stmt = stmt.offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return [
            {
                "id": row.id,
                "name": row.name,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "product_count": row.product_count,
            }
            for row in result.all()
        ]
