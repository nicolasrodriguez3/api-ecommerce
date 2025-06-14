from typing import Annotated, List
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session
from app.auth.dependencies import require_roles
from app.core import db_connection
from app.products import service
from app.products.schemas import (
    ProductImageResponse,
    ProductPublicResponse,
    PaginatedProductResponse,
    ProductCreate,
    ProductUpdate,
)
from app.users.models import User
from app.users.roles import RoleEnum

router = APIRouter(prefix="/products", tags=["Products"])

db: Session = db_connection.session

@router.get("/")
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, max_length=50),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    order_by: str = Query("id"),
    order_dir: str = Query("asc", pattern="^(asc|desc)$"),
) -> PaginatedProductResponse:
    products, page, total_pages = service.get_products(
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
def get_product(
    product_id: int
) -> ProductPublicResponse:
    return service.get_by_id(product_id)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_roles(RoleEnum.ADMIN))]
)
def create_product(
    product: ProductCreate,
) -> ProductPublicResponse:
    return service.create(product)


@router.put("/{product_id}")
def update_product(
    product_id: int, updated_data: ProductUpdate
):
    return service.update(product_id, updated_data)


@router.delete(
    "/{product_id}",
    status_code=204,
    dependencies=[Depends(require_roles(RoleEnum.ADMIN))],
)
def delete_product(
    product_id: int,
):
    return service.delete(product_id)


@router.patch(
    "/{product_id}/restore",
    status_code=200,
    dependencies=[Depends(require_roles(RoleEnum.ADMIN))],
)
def restore_product(
    product_id: int,
) -> ProductPublicResponse:
    return service.restore(product_id)


# Images
@router.post("/{product_id}/images", status_code=201)
async def upload_image(
    product_id: int,
    file: UploadFile = File(...),
) -> ProductImageResponse:
    return await service.upload_image(product_id, file)


@router.get("/{product_id}/images")
def get_images(
    product_id: int,
) -> List[ProductImageResponse]:
    return service.get_product_images(product_id)


@router.delete("/{product_id}/images/{image_id}", status_code=204)
def delete_image(
    product_id: int,
    image_id: int,
) -> None:
    return service.delete_image(product_id, image_id)


@router.patch("/images/{image_id}")
def update_image_position(
    image_id: int, new_position: int
) -> ProductImageResponse:
    return service.update_image_position(image_id, new_position)
