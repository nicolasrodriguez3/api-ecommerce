from app.core.exceptions import AppException, NotFoundError
from app.core.logger import setup_logger
from app.repositories.category import CategoryRepository
from app.schemas.category import (
    CategoryPublicResponse,
    CategoryQuery,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import PaginatedResponse, PaginationParams, PaginationRequest
from app.schemas.product import ProductPublicResponse

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
        self, query: CategoryQuery,
    ) -> PaginatedResponse[CategoryPublicResponse]:
        """Obtener lista de categorías con filtros opcionales, ordenamiento y paginación.

        Args:
            query: Objeto que contiene todos los parámetros de consulta

        Returns:
            PaginatedResponse: Lista paginada de categorías con metadata

        Raises:
            AppException: Si hay errores en la consulta
        """

        try:
            # Obtener categorías con filtros
            categories_db = await self.category_repo.get_categories_with_filters(query)
            
            # Obtener total de categorías con los mismos filtros
            total_categories = await self.category_repo.count_categories_with_filters(query.filters)

            # Convertir a response objects
            categories = [
                CategoryPublicResponse.model_validate(category) for category in categories_db
            ]

            logger.info(
                f"Retrieved {len(categories)} categories (page {query.pagination.page}, "
                f"total: {total_categories}) with filters: {query.filters.model_dump(exclude_none=True)}"
            )

            return PaginatedResponse(
                data=categories,
                total_elements=total_categories,
                page=query.pagination.page,
                per_page=query.pagination.per_page,
            )

        except Exception as e:
            logger.error(f"Error retrieving categories: {str(e)}")
            raise AppException(
                "Error al obtener categorías",
                code="categories_retrieval_error",
            ) from e

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
        await self.category_repo.category_soft_delete(category_id)
        
        logger.info(f"Soft deleted category with ID: {category_id}")
        return {"message": "Category deleted successfully", "category_id": category_id}



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