from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryResponse, PaginatedCategoryResponse


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.category_repo = CategoryRepository(db)

    async def get_by_id(self, category_id: int) -> CategoryResponse:
        category_db = await self.category_repo.get_by_id(category_id)
        if not category_db:
            raise NotFoundError("Product", category_id)

        return CategoryResponse.model_validate(category_db)

    async def get_categories(
        self, skip: int = 0, limit: int = 10
    ) -> PaginatedCategoryResponse:
        categories_db = await self.category_repo.get_multi(skip=skip, limit=limit)
        categories = [
            CategoryResponse.model_validate(category) for category in categories_db
        ]
        total_categories = await self.category_repo.count()

        return PaginatedCategoryResponse(
            data=categories,
            total_elements=total_categories,
            skip=skip,
            limit=limit,
        )
