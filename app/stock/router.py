from typing import Annotated, List
from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.stock.schemas import StockMovementCreate
from app.products.schemas import (
    ProductPublicResponse,
    StockHistoryResponse,
    StockUpdate,
)
from app.stock.service import adjust_stock
from app.products import service as product_service
from app.users.models import User
from app.users.roles import RoleEnum

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.post("/{product_id}", response_model=ProductPublicResponse)
def move_stock(
    product_id: int = Path(..., gt=0),
    movement: StockMovementCreate = Body(...),
):
    return adjust_stock(product_id, movement.quantity, movement.reason)


@router.patch(
    "/{product_id}/stock",
    response_model=ProductPublicResponse,
    dependencies=[Depends(require_roles(RoleEnum.ADMIN))],
)
def update_stock(
    product_id: int,
    stock_data: StockUpdate,
):
    return product_service.update_stock(product_id, stock_data.stock)


@router.get("/{product_id}/stock-history", response_model=List[StockHistoryResponse])
def get_stock_history(product_id: int):
    product = product_service._get_one_product(product_id)
    return product.stock_history
