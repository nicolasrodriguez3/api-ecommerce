from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundException, UnauthorizedException
from app.integrations.cianbox.schemas import SyncStatusResponse
from app.orders.models import Order
from app.orders.schemas import OrderCreate, OrderResponse
from app.orders import service
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
        return service.create_order(db, order_data, current_user.id)
    except ValueError as e:
        raise NotFoundException(str(e))


@router.get(
    "/",
    response_model=list[OrderResponse],
    dependencies=[Depends(require_roles(RoleEnum.ADMIN))],
)
def get_all_orders(db: Session = Depends(get_db)):
    return service.get_all_orders(db)


@router.get("/me", response_model=list[OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return service.get_order_by_user_id(db, current_user.id)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_order(db, order_id, current_user)


@router.post("/orders/{order_id}/sync/cianbox", response_model=SyncStatusResponse)
def sync_order_cianbox(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(dependency=get_current_user)):
    return service.sync_order_with_cianbox(db, order_id)
