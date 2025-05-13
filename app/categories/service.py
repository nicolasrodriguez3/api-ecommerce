from sqlalchemy.orm import Session
from app.categories import models, schemas
from app.core.exceptions import NotFoundException


def create_category(
    db: Session, category_data: schemas.CategoryCreate
) -> models.Category:
    category = models.Category(**category_data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_all_categories(db: Session) -> list[models.Category]:
    return db.query(models.Category).all()


def get_categories(
    db: Session, skip: int = 0, limit: int = 10
) -> tuple[list[models.Category], int]:
    query = db.query(models.Category)
    total = query.count()
    categories = query.offset(skip).limit(limit).all()
    return categories, total


def get_category_by_id(db: Session, category_id: int) -> models.Category:
    category = db.query(models.Category).filter_by(id=category_id).first()
    if not category:
        raise NotFoundException(f"Category with ID {category_id} not found")
    return category
