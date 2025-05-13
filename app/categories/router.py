from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.categories import schemas, service
from app.core.database import get_db

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return service.create_category(db, category)


@router.get("/", response_model=schemas.PaginatedCategoryResponse)
def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    categories, total = service.get_categories(db, skip=skip, limit=limit)
    return {"data": categories, "total": total}


@router.get("/{category_id}", response_model=schemas.CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    return service.get_category_by_id(db, category_id)
