from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.orders.models import Order
from app.orders.schemas import OrderCreate, OrderResponse
from app.orders.service import create_order
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.users.roles import RoleEnum
from app.auth.dependencies import require_roles

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse)
def create_order_endpoint(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_order(db, order_data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/",
    response_model=list[OrderResponse],
    dependencies=[Depends(require_roles(RoleEnum.ADMIN))],
)
def get_all_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()


@router.get("/me", response_model=list[OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(Order).filter(Order.user_id == current_user.id).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Solo admins o el mismo usuario pueden ver
    if order.user_id != current_user.id and current_user.role.name not in [
        "admin",
        "owner",
    ]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return order
