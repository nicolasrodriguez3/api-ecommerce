from app.core.exceptions import AppException, NotFoundError
from app.core.logger import setup_logger
from app.repositories.category import CategoryRepository
from app.schemas.category import (
    CategoryPublicResponse,
    PaginatedCategoryResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.product import PaginatedProductResponse, ProductPublicResponse

logger = setup_logger(__name__)


class CategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.category_repo = CategoryRepository(db)

    async def get_category_by_id(self, category_id: int) -> CategoryPublicResponse:
        """Obtener categoría por ID."""
        category_db = await self.category_repo.get_by_id(category_id)
        if not category_db:
            raise NotFoundError("Category", category_id)

        logger.info(f"Retrieved category with ID: {category_id}")
        return CategoryPublicResponse.model_validate(category_db)

    async def get_categories(
        self,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None,
        order_by: str = "id",
        order_dir: str = "asc",
        include_product_count: bool = False,
    ) -> PaginatedCategoryResponse:
        """Obtener lista de categorías con filtros opcionales, ordenamiento y paginación.

        Args:
            skip: Número de registros a saltar (para paginación)
            limit: Máximo número de categorías a devolver
            search: Término de búsqueda opcional para filtrar por nombre
            order_by: Campo por el cual ordenar los resultados (default: 'id')
            order_dir: Dirección del orden ('asc' o 'desc', default: 'asc')
            include_product_count: Incluir conteo de productos por categoría

        Returns:
            PaginatedCategoryResponse: Lista paginada de categorías con metadata

        Raises:
            AppException: Si el campo de ordenamiento no es válido
        """

        # Validar parámetros de ordenamiento
        ALLOWED_ORDER_FIELDS = {
            "id",
            "name",
            "created_at",
            "updated_at",
        }
        if order_by not in ALLOWED_ORDER_FIELDS:
            logger.error(
                f"Invalid order_by field: {order_by}. Allowed fields are: {', '.join(ALLOWED_ORDER_FIELDS)}"
            )
            raise AppException(
                f"Invalid order_by field. Allowed fields are: {', '.join(ALLOWED_ORDER_FIELDS)}",
                code="invalid_order_field",
            )

        # Validar dirección de ordenamiento
        if order_dir.lower() not in ["asc", "desc"]:
            logger.error(f"Invalid order_dir: {order_dir}. Must be 'asc' or 'desc'")
            raise AppException(
                "Invalid order direction. Must be 'asc' or 'desc'",
                code="invalid_order_direction",
            )

        # Crear filtros
        filters = {
            "search": search,
        }

        # Obtener categorías con filtros
        categories_db = await self.category_repo.get_categories_with_filters(
            skip=skip,
            limit=limit,
            filters=filters,
            order_by=order_by,
            order_dir=order_dir.lower(),
            include_product_count=include_product_count,
        )

        # Obtener total de categorías con los mismos filtros
        total_categories = await self.category_repo.count_categories_with_filters(filters)

        # Convertir a response objects
        categories = [
            CategoryPublicResponse.model_validate(category) for category in categories_db
        ]

        # Calcular metadata de paginación
        total_pages = total_categories // limit + (1 if total_categories % limit > 0 else 0)
        current_page = skip // limit + 1

        logger.info(
            f"Retrieved {len(categories)} categories (page {current_page}/{total_pages}, "
            f"total: {total_categories}) with filters: {filters}"
        )

        return PaginatedCategoryResponse(
            data=categories,
            total_elements=total_categories,
            skip=skip,
            limit=limit,
            current_page=current_page,
            total_pages=total_pages,
        )

    async def create_category(self, category_data) -> CategoryPublicResponse:
        """Crear nueva categoría."""
        category_dict = category_data.model_dump()

        # Validar nombre único
        await self._validate_unique_name(category_dict["name"])

        category_db = await self.category_repo.create(category_dict)
        
        logger.info(f"Created new category with ID: {category_db.id}")
        return CategoryPublicResponse.model_validate(category_db)

    async def update_category(self, category_id: int, category_data) -> CategoryPublicResponse:
        """Actualizar categoría existente."""
        # Verificar que la categoría existe
        category_db = await self.category_repo.get_by_id(category_id)
        if not category_db:
            raise NotFoundError("Category", category_id)

        category_dict = category_data.model_dump(exclude_unset=True)

        # Si se está actualizando el nombre, validar unicidad
        if "name" in category_dict and category_dict["name"] != category_db.name:
            await self._validate_unique_name(category_dict["name"])

        updated_category = await self.category_repo.update(category_id, category_dict)
        
        logger.info(f"Updated category with ID: {category_id}")
        return CategoryPublicResponse.model_validate(updated_category)

    async def delete_category(self, category_id: int) -> dict:
        """Eliminar categoría (soft delete).
        
        Validates that the category has no active products before deletion.
        """
        # Verificar que la categoría existe
        category_db = await self.category_repo.get_by_id(category_id)
        if not category_db:
            raise NotFoundError("Category", category_id)

        # Verificar que no tenga productos activos
        product_count = await self.category_repo.count_active_products_in_category(category_id)
        if product_count > 0:
            logger.error(
                f"Cannot delete category {category_id}: has {product_count} active products"
            )
            raise AppException(
                f"Cannot delete category. It has {product_count} active products. "
                "Please reassign or deactivate products first.",
                code="category_has_active_products",
            )

        # Realizar soft delete
        await self.category_repo.soft_delete(category_id)
        
        logger.info(f"Soft deleted category with ID: {category_id}")
        return {"message": "Category deleted successfully", "category_id": category_id}

    async def get_category_products(
        self,
        category_id: int,
        skip: int = 0,
        limit: int = 10,
        is_active: bool = True,
    ) -> PaginatedProductResponse:
        """Obtener productos de una categoría específica."""
        # Verificar que la categoría existe
        category_db = await self.category_repo.get_by_id(category_id)
        if not category_db:
            raise NotFoundError("Category", category_id)

        # Obtener productos de la categoría
        products_db = await self.category_repo.get_category_products(
            category_id=category_id,
            skip=skip,
            limit=limit,
            is_active=is_active,
        )

        # Obtener total de productos en la categoría
        total_products = await self.category_repo.count_products_in_category(
            category_id, is_active
        )

        # Convertir a response objects
        products = [
            ProductPublicResponse.model_validate(product) for product in products_db
        ]

        # Calcular metadata de paginación
        total_pages = total_products // limit + (1 if total_products % limit > 0 else 0)
        current_page = skip // limit + 1

        logger.info(
            f"Retrieved {len(products)} products from category {category_id} "
            f"(page {current_page}/{total_pages}, total: {total_products})"
        )

        return PaginatedProductResponse(
            data=products,
            total_elements=total_products,
            skip=skip,
            limit=limit,
            current_page=current_page,
            total_pages=total_pages,
        )

    async def _validate_unique_name(self, name: str) -> None:
        """Validar que el nombre de la categoría sea único."""
        existing_category = await self.category_repo.get_by_name(name)
        if existing_category:
            logger.error(f"Category name already exists: {name}")
            raise AppException(
                f"Category with name '{name}' already exists",
                code="category_name_exists",
            )

    async def _get_category(self, category_id: int):
        """Obtener categoría por ID (método interno)."""
        return await self.category_repo.get_by_id(category_id)