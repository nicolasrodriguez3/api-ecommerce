from typing import Any, Dict, List
from sqlalchemy import select, func, desc, asc, and_, or_
from app.core.exceptions import NotFoundError
from app.models.product import Product, ProductImage
from app.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload


class ProductRepository(BaseRepository[Product]):
    """Repositorio de productos con consultas específicas."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Product)

    async def get_by_name(self, name: str) -> Product | None:
        """Obtener producto por nombre."""
        stmt = select(Product).where(Product.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, obj_id: int) -> Product | None:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.images))
            .where(Product.id == obj_id)
        )
        return result.scalar_one_or_none()

    async def get_active_products(
        self, *, skip: int = 0, limit: int = 100
    ) -> list[Product]:
        """Obtener productos activos."""
        stmt = (
            select(Product).where(Product.is_active == True).offset(skip).limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Dict[str, Any] | None = None,
        order_by: str | None = None,
    ) -> List[Product]:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.images))  # Carga eager de images
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_products_with_filters(
        self,
        skip: int = 0,
        limit: int = 10,
        filters: Dict[str, Any] | None = None,
        order_by: str = "id",
        order_dir: str = "asc",
    ) -> List[Product]:
        """
        Obtener productos con filtros, ordenamiento y paginación.

        Args:
            skip: Registros a saltar
            limit: Límite de registros
            filters: Diccionario con filtros a aplicar
            order_by: Campo de ordenamiento
            order_dir: Dirección del ordenamiento ('asc' o 'desc')

        Returns:
            List[Product]: Lista de productos filtrados
        """
        # Construir query base con joins
        query = select(Product).options(
            joinedload(Product.category), joinedload(Product.images)
        )

        # Aplicar filtros
        if filters:
            conditions = []

            # Filtro por estado activo
            if filters.get("is_active") is not None:
                conditions.append(Product.is_active == filters["is_active"])

            # Filtro por búsqueda en nombre
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                conditions.append(Product.name.ilike(search_term))

            # Filtros de precio
            if filters.get("min_price") is not None:
                conditions.append(Product.price >= filters["min_price"])

            if filters.get("max_price") is not None:
                conditions.append(Product.price <= filters["max_price"])

            # Filtro por categoría
            if filters.get("category_id"):
                conditions.append(Product.category_id == filters["category_id"])

            # Aplicar todas las condiciones
            if conditions:
                query = query.where(and_(*conditions))

        # Aplicar ordenamiento
        if hasattr(Product, order_by):
            column = getattr(Product, order_by)
            if order_dir == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))

        # Aplicar paginación
        query = query.offset(skip).limit(limit)

        # Ejecutar query
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def count_products_with_filters(
        self, filters: Dict[str, Any] | None = None
    ) -> int:
        """
        Contar productos que coinciden con los filtros.

        Args:
            filters: Diccionario con filtros a aplicar

        Returns:
            int: Número total de productos que coinciden
        """
        # Query de conteo
        query = select(func.count(Product.id))

        # Aplicar los mismos filtros que en get_products_with_filters
        if filters:
            conditions = []

            if filters.get("is_active") is not None:
                conditions.append(Product.is_active == filters["is_active"])

            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                conditions.append(Product.name.ilike(search_term))

            if filters.get("min_price") is not None:
                conditions.append(Product.price >= filters["min_price"])

            if filters.get("max_price") is not None:
                conditions.append(Product.price <= filters["max_price"])

            if filters.get("category_id"):
                conditions.append(Product.category_id == filters["category_id"])

            if conditions:
                query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def search_products_advanced(
        self,
        skip: int = 0,
        limit: int = 10,
        search_term: str | None = None,
        filters: Dict[str, Any] | None = None,
        order_by: str = "id",
        order_dir: str = "asc",
    ) -> List[Product]:
        """
        Búsqueda avanzada de productos con múltiples campos.

        Args:
            skip: Registros a saltar
            limit: Límite de registros
            search_term: Término de búsqueda
            filters: Filtros adicionales
            order_by: Campo de ordenamiento
            order_dir: Dirección del ordenamiento

        Returns:
            List[Product]: Lista de productos encontrados
        """
        query = select(Product).options(
            joinedload(Product.category), joinedload(Product.images)
        )

        conditions = []

        # Búsqueda en múltiples campos
        if search_term:
            search = f"%{search_term}%"
            search_conditions = [
                Product.name.ilike(search),
                Product.description.ilike(search),
                # También buscar en categoría si está relacionada
            ]
            conditions.append(or_(*search_conditions))

        # Aplicar filtros adicionales
        if filters:
            if filters.get("is_active") is not None:
                conditions.append(Product.is_active == filters["is_active"])

            if filters.get("min_price") is not None:
                conditions.append(Product.price >= filters["min_price"])

            if filters.get("max_price") is not None:
                conditions.append(Product.price <= filters["max_price"])

            if filters.get("category_id"):
                conditions.append(Product.category_id == filters["category_id"])

        if conditions:
            query = query.where(and_(*conditions))

        # Ordenamiento
        if hasattr(Product, order_by):
            column = getattr(Product, order_by)
            query = query.order_by(desc(column) if order_dir == "desc" else asc(column))

        # Paginación
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def create_image(self, product_id: int, image) -> ProductImage:
        """Crea una nueva imagen de un producto."""
        image_db = ProductImage(
            product_id=product_id,
            url=image.url,
            public_id=image.public_id,
            position=image.position,
        )
        self.db.add(image_db)
        await self.db.commit()
        await self.db.refresh(image_db)
        return image_db

    async def get_images_by_product_id(self, product_id: int):
        """Obtiene todas las imágenes de un producto por su ID."""
        stmt = select(ProductImage).where(ProductImage.product_id == product_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_image_by_id(self, image_id: int) -> ProductImage | None:
        """Obtiene una imagen por su ID."""
        stmt = select(ProductImage).where(ProductImage.id == image_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_image_by_position(
        self, product_id: int, position: int
    ) -> ProductImage | None:
        """
        Obtiene una imagen por su posición en un producto específico.

        Args:
            product_id: ID del producto
            position: Posición de la imagen

        Returns:
            ProductImage | None: Imagen encontrada o None
        """
        result = await self.db.execute(
            select(ProductImage).where(
                ProductImage.product_id == product_id, ProductImage.position == position
            )
        )
        return result.scalar_one_or_none()

    async def update_image_position(
        self, image_id: int, new_position: int
    ) -> ProductImage:
        """
        Actualiza la posición de una imagen.

        Args:
            image_id: ID de la imagen
            new_position: Nueva posición

        Returns:
            ProductImage: Imagen actualizada

        Raises:
            NotFoundError: Si la imagen no existe
        """
        # Obtener la imagen
        result = await self.db.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        image = result.scalar_one_or_none()

        if not image:
            raise NotFoundError("Image", image_id)

        # Actualizar la posición
        image.position = new_position

        # Confirmar cambios
        await self.db.commit()
        await self.db.refresh(image)

        return image

    # Alternativa más eficiente usando una sola transacción:
    async def swap_image_positions(
        self, image1_id: int, image2_id: int, new_pos1: int, new_pos2: int
    ) -> tuple[ProductImage, ProductImage]:
        """
        Intercambia las posiciones de dos imágenes en una sola transacción.

        Args:
            image1_id: ID de la primera imagen
            image2_id: ID de la segunda imagen
            new_pos1: Nueva posición para la primera imagen
            new_pos2: Nueva posición para la segunda imagen

        Returns:
            tuple[ProductImage, ProductImage]: Ambas imágenes actualizadas
        """
        # Obtener ambas imágenes
        result1 = await self.db.execute(
            select(ProductImage).where(ProductImage.id == image1_id)
        )
        result2 = await self.db.execute(
            select(ProductImage).where(ProductImage.id == image2_id)
        )

        image1 = result1.scalar_one_or_none()
        image2 = result2.scalar_one_or_none()

        if not image1:
            raise NotFoundError("Image", image1_id)
        if not image2:
            raise NotFoundError("Image", image2_id)

        # Actualizar posiciones
        image1.position = new_pos1
        image2.position = new_pos2

        # Confirmar cambios
        await self.db.commit()
        await self.db.refresh(image1)
        await self.db.refresh(image2)

        return image1, image2
