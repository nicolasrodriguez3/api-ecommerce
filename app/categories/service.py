from sqlalchemy.orm import Session
from app.categories import models, schemas
from app.core.exceptions import ConflictException, NotFoundException


def create_category(
    db: Session, category_data: schemas.CategoryCreate
) -> schemas.CategoryResponse:
    name: str = category_data.name

    existing = db.query(models.Category).filter_by(name=name).first()
    if existing:
        raise ConflictException(f"Category with name '{name}' already exists")

    category = models.Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return schemas.CategoryResponse.model_validate(category)


def get_all_categories(db: Session) -> list[schemas.CategoryResponse]:
    categories = db.query(models.Category).all()
    
    return [schemas.CategoryResponse.model_validate(c) for c in categories]



def get_categories(
    db: Session, skip: int = 0, limit: int = 10
) -> schemas.PaginatedCategoryResponse:
    query = db.query(models.Category)
    total = query.count()
    categories = query.offset(skip).limit(limit).all()
    categories = [schemas.CategoryResponse.model_validate(c) for c in categories]
    
    return schemas.PaginatedCategoryResponse(data=categories, total=total)


def get_category_by_id(db: Session, category_id: int) -> schemas.CategoryResponse:
    category = db.query(models.Category).filter_by(id=category_id).first()
    if not category:
        raise NotFoundException(f"Category with ID {category_id} not found")
    return schemas.CategoryResponse.model_validate(category)
