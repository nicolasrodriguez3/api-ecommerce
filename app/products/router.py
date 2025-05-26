from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.products import service
from app.products.schemas import (
    ProductPublicResponse,
    PaginatedProductResponse,
    ProductCreate,
)
from app.users.models import User
from app.users.roles import RoleEnum

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/")
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, max_length=50),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    order_by: str = Query("id"),
    order_dir: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> PaginatedProductResponse:
    products, page, total_pages = service.get_products(
        db,
        skip=skip,
        limit=limit,
        search=search,
        min_price=min_price,
        max_price=max_price,
        order_by=order_by,
        order_dir=order_dir,
    )

    return PaginatedProductResponse(
        data=products,
        page=page,
        total_pages=total_pages,
    )


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductPublicResponse:
    return service.get_by_id(db, product_id)


@router.post("/", status_code=201)
def create_product(
    current_user: Annotated[User, Depends(require_roles(RoleEnum.admin))],
    product: ProductCreate,
    db: Session = Depends(get_db),
) -> ProductPublicResponse:
    return service.create(product, db)


@router.put("/{product_id}")
def update_product(
    product_id: int, updated_data: ProductCreate, db: Session = Depends(get_db)
) -> ProductPublicResponse:
    return service.update(product_id, updated_data, db)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.admin))],
    db: Session = Depends(get_db),
):
    return service.delete(product_id, db)


@router.patch("/{product_id}/restore", status_code=200)
def restore_product(
    product_id: int,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.admin))],
    db: Session = Depends(get_db),
) -> ProductPublicResponse:
    return service.restore(product_id, db)
