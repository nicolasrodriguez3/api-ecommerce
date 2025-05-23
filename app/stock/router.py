from typing import Annotated, List
from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.stock.schemas import StockMovementCreate
from app.products.schemas import ProductResponse, StockHistoryResponse, StockUpdate
from app.stock.service import adjust_stock
from app.products import service as product_service
from app.users.models import User
from app.users.roles import RoleEnum

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.post("/{product_id}", response_model=ProductResponse)
def move_stock(
    product_id: int = Path(..., gt=0),
    movement: StockMovementCreate = Body(...),
    db: Session = Depends(get_db),
):
    return adjust_stock(db, product_id, movement.quantity, movement.reason)


@router.patch("/{product_id}/stock", response_model=ProductResponse)
def update_stock(
    product_id: int,
    stock_data: StockUpdate,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.admin))],
    db: Session = Depends(get_db),
):
    return product_service.update_stock(db, product_id, stock_data.stock)


@router.get("/{product_id}/stock-history", response_model=List[StockHistoryResponse])
def get_stock_history(product_id: int, db: Session = Depends(get_db)):
    product = product_service._get_one_product(db, product_id)
    return product.stock_history
