from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.products import schemas, service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=schemas.PaginatedProductResponse)
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, max_length=50),
    order_by: str = Query("id"),
    order_dir: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    products, total = service.get_products(
        db, skip=skip, limit=limit, search=search,
        order_by=order_by, order_dir=order_dir
    )
    return {"data": products, "total": total}


@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return service.get_by_id(db, product_id)


@router.post("/", response_model=schemas.ProductResponse, status_code=201)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return service.create(product, db)


@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int, updated_data: schemas.ProductCreate, db: Session = Depends(get_db)
):
    return service.update(product_id, updated_data, db)


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    service.delete(product_id, db)
