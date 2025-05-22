from typing import Annotated, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.core.exceptions import BadRequestException
from app.products import service
from app.products.schemas import (
    ProductResponse,
    PaginatedProductResponse,
    ProductCreate,
    StockAdjustment,
    StockHistoryResponse,
    StockUpdate,
)
from app.users.models import User
from app.users.roles import RoleEnum

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=PaginatedProductResponse)
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, max_length=50),
    order_by: str = Query("id"),
    order_dir: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    products, total = service.get_products(
        db,
        skip=skip,
        limit=limit,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
    )
    return {"data": products, "total": total}


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return service.get_by_id(db, product_id)


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(current_user: Annotated[User, Depends(require_roles(RoleEnum.admin))], product: ProductCreate, db: Session = Depends(get_db) ):
    return service.create(product, db)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, updated_data: ProductCreate, db: Session = Depends(get_db)
):
    return service.update(product_id, updated_data, db)


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    service.delete(product_id, db)


@router.patch("/{product_id}/restore", status_code=204)
def restore_product(product_id: int, db: Session = Depends(get_db)):
    service.restore(product_id, db)


@router.patch("/{product_id}/stock", response_model=ProductResponse)
def update_stock(
    product_id: int,
    stock_data: StockUpdate,
    db: Session = Depends(get_db),
):
    return service.update_stock(db, product_id, stock_data.stock)


@router.patch("/{product_id}/increase-stock", response_model=ProductResponse)
def increase_stock(
    product_id: int,
    data: StockAdjustment,
    db: Session = Depends(get_db),
) -> ProductResponse:
    if data.quantity <= 0:
        raise BadRequestException("Quantity must be greater than 0")
    return service.adjust_stock(db, product_id, data.quantity)


@router.patch("/{product_id}/decrease-stock", response_model=ProductResponse)
def decrease_stock(
    product_id: int,
    data: StockAdjustment,
    db: Session = Depends(get_db),
) -> ProductResponse:
    if data.quantity <= 0:
        raise BadRequestException("Quantity must be greater than 0")
    return service.adjust_stock(db, product_id, -data.quantity)
