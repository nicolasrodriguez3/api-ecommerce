from sqlalchemy import select
from app.models.product import Category
from app.repositories.base import BaseRepository
from sqlalchemy.orm import Session

class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session):
        super().__init__(db, Category)