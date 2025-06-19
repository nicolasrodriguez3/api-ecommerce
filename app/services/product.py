from app.core.exceptions import NotFoundError
from app.models.category import Category
from app.repositories.product import ProductRepository
from app.schemas.product import PaginatedProductResponse, ProductPublicResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.category import CategoryService


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_service = CategoryService(db)

    async def get_product_by_id(self, product_id):
        product_db = await self.product_repo.get_by_id(product_id)
        if not product_db:
            raise NotFoundError("Product", product_id)

        return ProductPublicResponse.model_validate(product_db)

    async def get_products(
        self, skip: int = 0, limit: int = 100
    ) -> PaginatedProductResponse:
        """Obtener lista de productos con paginación.
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a devolver
        Returns:
            PaginatedProductsResponse: Lista de productos paginada
        """
        products_db = await self.product_repo.get_multi(skip=skip, limit=limit)

        products = [
            ProductPublicResponse.model_validate(product) for product in products_db
        ]

        total_products = await self.product_repo.count()

        return PaginatedProductResponse(
            data=products, total_elements=total_products, skip=skip, limit=limit
        )

    async def create_product(self, product_data) -> ProductPublicResponse:
        product_dict = product_data.model_dump()

        category_id: int | None = product_dict.get("category_id")
        if category_id is None or category_id <= 0:
            product_dict["category_id"] = 1
        else:
            category = await self._get_category(category_id)
            if not category:
                raise NotFoundError("Category", category_id)

        product_db = await self.product_repo.create(product_dict)
        return ProductPublicResponse.model_validate(product_db)

    async def update_product(self, product_id, product_data) -> ProductPublicResponse:
        product_dict: dict = product_data.model_dump()

        category_id: int | None = product_dict.get("category_id")
        if category_id is None or category_id <= 0:
            product_dict["category_id"] = 1
        else:
            category = await self._get_category(category_id)
            if not category:
                raise NotFoundError("Category", category_id)

        product_db = await self.product_repo.update(product_id, product_dict)
        return ProductPublicResponse.model_validate(product_db)

    async def delete_product(self, product_id):
        return await self.product_repo.delete(product_id)

    async def _get_category(self, category_id: int):
        """Obtener categoría por ID."""
        return await self.category_service.get_by_id(category_id)
