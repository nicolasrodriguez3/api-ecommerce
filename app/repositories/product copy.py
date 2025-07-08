from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select, func, desc, asc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from dataclasses import dataclass
from enum import Enum

from app.core.exceptions import NotFoundError
from app.models.product import Product, ProductImage
from app.repositories.base import BaseRepository
from app.schemas.product import ProductCreate


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class ProductFilters:
    """Filtros tipados para mejor validación"""
    is_active: Optional[bool] = None
    search: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    category_id: Optional[int] = None
    category_ids: Optional[List[int]] = None  # Para múltiples categorías


@dataclass
class ProductQuery:
    """Parámetros de consulta unificados"""
    filters: Optional[ProductFilters] = None
    order_by: str = "id"
    order_direction: SortDirection = SortDirection.ASC
    include_images: bool = True
    include_category: bool = True


class ProductRepository(BaseRepository[Product]):
    """Repositorio optimizado de productos"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Product)

    # === MÉTODOS DE CONSULTA PRINCIPALES ===
    
    async def find_by_id(self, product_id: int, include_relations: bool = True) -> Optional[Product]:
        """Buscar producto por ID con relaciones opcionales"""
        query = select(Product).where(Product.id == product_id)
        
        if include_relations:
            query = query.options(
                selectinload(Product.images),
                selectinload(Product.category)
            )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_by_name(self, name: str) -> Optional[Product]:
        """Buscar producto por nombre exacto"""
        result = await self.db.execute(
            select(Product).where(Product.name == name)
        )
        return result.scalar_one_or_none()

    async def search_products(
        self,
        query_params: ProductQuery,
        pagination: Optional[PaginationParams] = None
    ) -> Union[List[Product], PaginatedResponse]:
        """
        Método unificado para búsqueda de productos
        Reemplaza get_active_products, get_products_with_filters, etc.
        """
        query = self._build_base_query(query_params)
        query = self._apply_filters(query, query_params.filters)
        query = self._apply_ordering(query, query_params.order_by, query_params.order_direction)

        if pagination:
            return await self._execute_paginated_query(query, pagination, query_params)
        else:
            result = await self.db.execute(query)
            return list(result.scalars().unique().all())

    async def count_products(self, filters: Optional[ProductFilters] = None) -> int:
        """Contar productos con filtros"""
        query = select(func.count(Product.id))
        query = self._apply_filters(query, filters)
        
        result = await self.db.execute(query)
        return result.scalar() or 0

    # === MÉTODOS PRIVADOS DE CONSTRUCCIÓN DE QUERIES ===
    
    def _build_base_query(self, query_params: ProductQuery):
        """Construir query base con relaciones opcionales"""
        query = select(Product)
        
        options = []
        if query_params.include_images:
            options.append(selectinload(Product.images))
        if query_params.include_category:
            options.append(selectinload(Product.category))
        
        if options:
            query = query.options(*options)
            
        return query

    def _apply_filters(self, query, filters: Optional[ProductFilters]):
        """Aplicar filtros de forma centralizada"""
        if not filters:
            return query

        conditions = []

        # Filtro de estado activo
        if filters.is_active is not None:
            conditions.append(Product.is_active == filters.is_active)

        # Búsqueda de texto
        if filters.search:
            search_term = f"%{filters.search.strip()}%"
            search_conditions = [
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            ]
            conditions.append(or_(*search_conditions))

        # Filtros de precio
        if filters.min_price is not None:
            conditions.append(Product.price >= filters.min_price)
        if filters.max_price is not None:
            conditions.append(Product.price <= filters.max_price)

        # Filtro de categoría (simple)
        if filters.category_id:
            conditions.append(Product.category_id == filters.category_id)
        
        # Filtro de múltiples categorías
        if filters.category_ids:
            conditions.append(Product.category_id.in_(filters.category_ids))

        if conditions:
            query = query.where(and_(*conditions))

        return query

    def _apply_ordering(self, query, order_by: str, direction: SortDirection):
        """Aplicar ordenamiento de forma segura"""
        if not hasattr(Product, order_by):
            order_by = "id"  # Fallback seguro
        
        column = getattr(Product, order_by)
        
        if direction == SortDirection.DESC:
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))
            
        return query

    async def _execute_paginated_query(
        self, 
        query, 
        pagination: PaginationParams, 
        query_params: ProductQuery
    ) -> PaginatedResponse:
        """Ejecutar query con paginación cursor-based"""
        # Implementar cursor-based pagination aquí
        # (usando el código del primer artifact)
        pass

    # === MÉTODOS DE CREACIÓN Y ACTUALIZACIÓN ===
    
    async def create_product(self, product_data: ProductCreate) -> Product:
        """Crear producto con manejo de errores mejorado"""
        try:
            product = Product(**product_data.model_dump(exclude_unset=True))
            self.db.add(product)
            await self.db.commit()
            await self.db.refresh(product)
            return product
        except Exception:
            await self.db.rollback()
            raise

    async def update_product(
        self, 
        product_id: int, 
        update_data: Dict[str, Any]
    ) -> Product:
        """Actualizar producto existente"""
        product = await self.find_by_id(product_id, include_relations=False)
        if not product:
            raise NotFoundError("Product", product_id)

        try:
            for field, value in update_data.items():
                if hasattr(product, field):
                    setattr(product, field, value)
            
            await self.db.commit()
            await self.db.refresh(product)
            return product
        except Exception:
            await self.db.rollback()
            raise

    # === MÉTODOS DE IMÁGENES (Ya optimizados en tu código) ===
    
    async def add_product_image(
        self, 
        product_id: int, 
        image_data: Dict[str, Any]
    ) -> ProductImage:
        """Agregar imagen a producto"""
        # Verificar que el producto existe
        product = await self.find_by_id(product_id, include_relations=False)
        if not product:
            raise NotFoundError("Product", product_id)

        try:
            image = ProductImage(product_id=product_id, **image_data)
            self.db.add(image)
            await self.db.commit()
            await self.db.refresh(image)
            return image
        except Exception:
            await self.db.rollback()
            raise