from typing import Any, Dict, List, Optional, Sequence
from sqlalchemy import select, func, desc, asc, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from dataclasses import dataclass

from app.core.exceptions import NotFoundError
from app.models.product import Product, ProductImage
from app.repositories.base import BaseRepository
from app.schemas.product import ProductCreate


@dataclass(frozen=True)
class ProductFilters:
    """Value object para encapsular filtros de productos."""
    search: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = True

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario excluyendo valores None."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass(frozen=True)
class SortOptions:
    """Value object para opciones de ordenamiento."""
    field: str = "id"
    direction: str = "asc"

    def __post_init__(self):
        ALLOWED_FIELDS = {"id", "name", "price", "stock", "created_at", "updated_at"}
        if self.field not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid sort field: {self.field}")
        if self.direction.lower() not in ["asc", "desc"]:
            raise ValueError(f"Invalid sort direction: {self.direction}")


@dataclass(frozen=True)
class PaginationParams:
    """Value object para parámetros de paginación."""
    offset: int = 0
    limit: int = 10
    
    def __post_init__(self):
        if self.offset < 0:
            raise ValueError("Offset must be >= 0")
        if self.limit < 1 or self.limit > 100:
            raise ValueError("Limit must be between 1 and 100")


class ProductRepository(BaseRepository[Product]):
    """Repositorio de productos con consultas específicas."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Product)

    async def get_by_name(self, name: str) -> Optional[Product]:
        """Obtener producto por nombre."""
        stmt = select(Product).where(Product.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_relations(self, obj_id: int) -> Optional[Product]:
        """Obtener producto por ID con relaciones cargadas."""
        stmt = (
            select(Product)
            .options(
                selectinload(Product.images),
                selectinload(Product.category)
            )
            .where(Product.id == obj_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_products(
        self, 
        pagination: PaginationParams
    ) -> List[Product]:
        """Obtener productos activos con paginación."""
        stmt = (
            select(Product)
            .where(Product.is_active == True)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _build_base_query(self):
        """Construye la query base con joins optimizados."""
        return select(Product).options(
            selectinload(Product.images),
            selectinload(Product.category)
        )

    def _apply_filters(self, query, filters: ProductFilters):
        """Aplica filtros a la query de forma optimizada."""
        conditions = []

        if filters.is_active is not None:
            conditions.append(Product.is_active == filters.is_active)

        if filters.search:
            # Usar índice de texto completo si está disponible
            search_term = f"%{filters.search.strip()}%"
            search_conditions = [
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            ]
            conditions.append(or_(*search_conditions))

        if filters.min_price is not None:
            conditions.append(Product.price >= filters.min_price)

        if filters.max_price is not None:
            conditions.append(Product.price <= filters.max_price)

        if filters.category_id:
            conditions.append(Product.category_id == filters.category_id)

        if conditions:
            query = query.where(and_(*conditions))

        return query

    def _apply_sorting(self, query, sort: SortOptions):
        """Aplica ordenamiento a la query."""
        column = getattr(Product, sort.field)
        if sort.direction.lower() == "desc":
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))
        return query

    def _apply_pagination(self, query, pagination: PaginationParams):
        """Aplica paginación a la query."""
        return query.offset(pagination.offset).limit(pagination.limit)

    async def find_with_filters(
        self,
        filters: ProductFilters,
        sort: SortOptions,
        pagination: PaginationParams
    ) -> List[Product]:
        """
        Busca productos aplicando filtros, ordenamiento y paginación.
        
        Args:
            filters: Filtros a aplicar
            sort: Opciones de ordenamiento
            pagination: Parámetros de paginación
            
        Returns:
            Lista de productos filtrados
        """
        query = self._build_base_query()
        query = self._apply_filters(query, filters)
        query = self._apply_sorting(query, sort)
        query = self._apply_pagination(query, pagination)

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def count_with_filters(self, filters: ProductFilters) -> int:
        """
        Cuenta productos que coinciden con los filtros.
        
        Args:
            filters: Filtros a aplicar
            
        Returns:
            Número total de productos que coinciden
        """
        query = select(func.count(Product.id))
        query = self._apply_filters(query, filters)
        
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def search_full_text(
        self,
        search_term: str,
        filters: ProductFilters,
        sort: SortOptions,
        pagination: PaginationParams
    ) -> List[Product]:
        """
        Búsqueda de texto completo optimizada.
        
        Args:
            search_term: Término de búsqueda
            filters: Filtros adicionales
            sort: Opciones de ordenamiento
            pagination: Parámetros de paginación
            
        Returns:
            Lista de productos encontrados
        """
        # Para PostgreSQL con índices de texto completo
        # query = select(Product).where(
        #     text("to_tsvector('spanish', name || ' ' || description) @@ plainto_tsquery('spanish', :search)")
        # ).params(search=search_term)
        
        # Versión compatible con múltiples DBMS
        query = self._build_base_query()
        
        search = f"%{search_term.strip()}%"
        search_conditions = [
            Product.name.ilike(search),
            Product.description.ilike(search)
        ]
        
        # Crear filtros con búsqueda
        search_filters = ProductFilters(
            search=search_term,
            min_price=filters.min_price,
            max_price=filters.max_price,
            category_id=filters.category_id,
            is_active=filters.is_active
        )
        
        query = self._apply_filters(query, search_filters)
        query = self._apply_sorting(query, sort)
        query = self._apply_pagination(query, pagination)

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def create_with_validation(self, product_data: ProductCreate) -> Product:
        """Crea un producto con validaciones."""
        # Validar nombre único
        existing = await self.get_by_name(product_data.name)
        if existing:
            raise ValueError(f"Product with name '{product_data.name}' already exists")
            
        product = Product(**product_data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    # Métodos para gestión de imágenes
    async def create_image(self, product_id: int, image_data: dict) -> ProductImage:
        """Crea una nueva imagen de producto."""
        # Obtener siguiente posición
        stmt = select(func.coalesce(func.max(ProductImage.position), 0) + 1).where(
            ProductImage.product_id == product_id
        )
        result = await self.db.execute(stmt)
        next_position = result.scalar()

        image = ProductImage(
            product_id=product_id,
            position=next_position,
            **image_data
        )
        
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def get_images_by_product_id(self, product_id: int) -> List[ProductImage]:
        """Obtiene imágenes ordenadas por posición."""
        stmt = (
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.position)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_image_by_id(self, image_id: int) -> Optional[ProductImage]:
        """Obtiene imagen por ID."""
        stmt = select(ProductImage).where(ProductImage.id == image_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def reorder_images(self, product_id: int, image_positions: Dict[int, int]):
        """
        Reordena múltiples imágenes en una transacción.
        
        Args:
            product_id: ID del producto
            image_positions: Dict {image_id: new_position}
        """
        for image_id, new_position in image_positions.items():
            stmt = (
                select(ProductImage)
                .where(
                    ProductImage.id == image_id,
                    ProductImage.product_id == product_id
                )
            )
            result = await self.db.execute(stmt)
            image = result.scalar_one_or_none()
            
            if image:
                image.position = new_position

        await self.db.commit()

    async def delete_image_cascade(self, image_id: int) -> bool:
        """
        Elimina imagen y reorganiza posiciones.
        
        Args:
            image_id: ID de la imagen a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        # Obtener imagen
        image = await self.get_image_by_id(image_id)
        if not image:
            return False

        product_id = image.product_id
        deleted_position = image.position

        # Eliminar imagen
        await self.db.delete(image)

        # Reorganizar posiciones posteriores
        stmt = (
            select(ProductImage)
            .where(
                ProductImage.product_id == product_id,
                ProductImage.position > deleted_position
            )
        )
        result = await self.db.execute(stmt)
        images_to_update = result.scalars().all()

        for img in images_to_update:
            img.position -= 1

        await self.db.commit()
        return True

    async def get_product_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de productos."""
        stats_query = select(
            func.count(Product.id).label('total_products'),
            func.count(Product.id).filter(Product.is_active == True).label('active_products'),
            func.avg(Product.price).label('avg_price'),
            func.min(Product.price).label('min_price'),
            func.max(Product.price).label('max_price'),
            func.sum(Product.stock).label('total_stock')
        )
        
        result = await self.db.execute(stats_query)
        row = result.first()
        
        return {
            'total_products': row.total_products or 0,
            'active_products': row.active_products or 0,
            'avg_price': float(row.avg_price or 0),
            'min_price': float(row.min_price or 0),
            'max_price': float(row.max_price or 0),
            'total_stock': row.total_stock or 0
        }

    async def get_low_stock_products(self, threshold: int = 5) -> List[Product]:
        """Obtiene productos con stock bajo."""
        stmt = (
            select(Product)
            .where(
                Product.stock <= threshold,
                Product.is_active == True
            )
            .order_by(Product.stock)
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())