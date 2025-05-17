from typing import List
from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.stock.schemas import StockMovementCreate
from app.products.schemas import ProductResponse, StockHistoryResponse
from app.stock.service import adjust_stock
from app.products import service as product_service

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.post("/{product_id}", response_model=ProductResponse)
def move_stock(
    product_id: int = Path(..., gt=0),
    movement: StockMovementCreate = Body(...),
    db: Session = Depends(get_db),
):
    return adjust_stock(db, product_id, movement.quantity, movement.reason)

@router.get("/{product_id}/stock-history", response_model=List[StockHistoryResponse])
def get_stock_history(product_id: int, db: Session = Depends(get_db)):
    product = product_service._get_one_product(db, product_id)
    return product.stock_history

