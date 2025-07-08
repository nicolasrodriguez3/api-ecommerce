from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select, func, desc, asc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.product import Product, ProductImage
from app.repositories.base import BaseRepository
from app.schemas.common import (
    PaginatedResponse,
    PaginationParams,
    SortDirection,
)
from app.schemas.product import ProductCreate, ProductFilters, ProductQuery
from app.utils.pagination import CursorUtils


class ProductRepository(BaseRepository[Product]):
    """Repositorio optimizado de productos"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Product)

    # === MÉTODOS DE CONSULTA PRINCIPALES ===

    async def find_by_id(
        self, product_id: int, include_relations: bool = True
    ) -> Optional[Product]:
        """Buscar producto por ID con relaciones opcionales"""
        query = select(Product).where(Product.id == product_id)

        if include_relations:
            query = query.options(
                selectinload(Product.images), selectinload(Product.category)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_by_name(self, name: str) -> Optional[Product]:
        """Buscar producto por nombre exacto"""
        result = await self.db.execute(select(Product).where(Product.name == name))
        return result.scalar_one_or_none()

    async def search_products(
        self, query_params: ProductQuery, pagination: Optional[PaginationParams] = None
    ) -> Union[List[Product], PaginatedResponse]:
        """
        Método unificado para búsqueda de productos
        Reemplaza get_active_products, get_products_with_filters, etc.
        """
        query = self._build_base_query(query_params)
        query = self._apply_filters(query, query_params.filters)
        query = self._apply_ordering(
            query, query_params.order_by, query_params.order_direction
        )

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
                Product.description.ilike(search_term),
            ]
            conditions.append(or_(*search_conditions))

        # Filtros de precio
        if filters.min_price is not None:
            conditions.append(Product.price >= filters.min_price)
        if filters.max_price is not None:
            conditions.append(Product.price <= filters.max_price)

        # Filtro de categoría (simple)
        # if filters.category_id:
        #     conditions.append(Product.category_id == filters.category_id)

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
        self, query, pagination: PaginationParams, query_params: ProductQuery
    ) -> PaginatedResponse:
        """Ejecutar query con paginación cursor-based"""
        # Query base
        query = select(Product).options(
            selectinload(Product.images), selectinload(Product.category)
        )

        # Aplicar filtros
        query = self._apply_filters(query, query_params.filters)

        # Determinar columna de ordenamiento
        order_column = getattr(Product, query_params.order_by, Product.id)
        is_desc = query_params.order_direction.lower() == "desc"

        # Aplicar cursor si existe
        if pagination.cursor:
            cursor_value = CursorUtils.decode_cursor(pagination.cursor)
            if pagination.direction == "next":
                if is_desc:
                    query = query.where(order_column < cursor_value)
                else:
                    query = query.where(order_column > cursor_value)
            else:  # prev
                if is_desc:
                    query = query.where(order_column > cursor_value)
                else:
                    query = query.where(order_column < cursor_value)

        # Aplicar ordenamiento
        if is_desc:
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # Obtener un registro extra para saber si hay más páginas
        query = query.limit(pagination.limit + 1)

        # Ejecutar query
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        # Determinar si hay más páginas
        has_next = len(items) > pagination.limit
        if has_next:
            items = items[:-1]  # Remover el registro extra

        # Generar cursors
        next_cursor = None
        prev_cursor = None

        if items:
            if has_next:
                next_cursor = CursorUtils.create_cursor(
                    getattr(items[-1], query_params.order_by)
                )
            if pagination.cursor:  # Si llegamos desde un cursor, hay página anterior
                prev_cursor = CursorUtils.create_cursor(
                    getattr(items[0], query_params.order_by)
                )

        # Contar total solo si es necesario (costoso)
        total_count = None
        if query_params.include_total:
            count_query = select(func.count(Product.id))
            count_query = self._apply_filters(count_query, query_params.filters)
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()

        return PaginatedResponse(
            items=items,
            has_next=has_next,
            has_prev=pagination.cursor is not None,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            total_count=total_count,
        )

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
        self, product_id: int, update_data: Dict[str, Any]
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
        self, product_id: int, image_data: Dict[str, Any]
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
