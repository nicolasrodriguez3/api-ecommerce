from fastapi import APIRouter, Depends, status
from app.core.exceptions import NotFoundException, UnauthorizedException
from app.integrations.cianbox.schemas import SyncStatusResponse
from app.orders.models import Order
from app.orders.schemas import OrderCreate, OrderResponse
from app.orders import service
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.users.roles import RoleEnum
from app.auth.dependencies import require_roles

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse)
def create_order_endpoint(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
):
    try:
        return service.create_order(order_data, current_user.id)
    except ValueError as e:
        raise NotFoundException(str(e))


@router.get(
    "/",
    response_model=list[OrderResponse],
    dependencies=[Depends(require_roles(RoleEnum.ADMIN))],
)
def get_all_orders():
    return service.get_all_orders()


@router.get("/me", response_model=list[OrderResponse])
def get_my_orders(
    current_user: User = Depends(get_current_user)
):
    return service.get_order_by_user_id(current_user.id)


@router.get("/{order_id}")
def get_order_by_id(
    order_id: int,
    current_user: User = Depends(get_current_user),
):
    return service.get_order(order_id, current_user)


@router.post(
    "/orders/{order_id}/sync/cianbox",
    response_model=SyncStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_roles(RoleEnum.ADMIN, RoleEnum.SELLER))],
)
def sync_order_cianbox(
    order_id: int,
):
    return service.sync_order_with_cianbox(order_id)
