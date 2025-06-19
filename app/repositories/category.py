from sqlalchemy import select
from app.models.product import Category
from app.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Category)