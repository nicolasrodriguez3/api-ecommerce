from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.categories import schemas, service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate):
    return service.create_category(category)


@router.get("/", response_model=schemas.PaginatedCategoryResponse)
def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return service.get_categories(skip=skip, limit=limit)


@router.get("/{category_id}", response_model=schemas.CategoryResponse)
def get_category(category_id: int):
    return service.get_category_by_id(category_id)
