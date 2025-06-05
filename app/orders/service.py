from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import BadRequestException, NotFoundException, UnauthorizedException
from app.integrations.cianbox.schemas import SyncResponse, SyncStatusResponse
from app.integrations.cianbox.sync_order import sync_order
from app.orders.models import Order, OrderItem, SyncStatus
from app.orders.schemas import OrderCreate
from app.products.models import Product
from app.models.user import User
from app.users.roles import RoleEnum
from app.core import db_connection

db: Session = db_connection.session

def create_order(order_data: OrderCreate, user_id: int) -> Order:
    new_order = Order(
        user_id=user_id,
        total_amount=0.0,  # Inicialmente 0, se actualizará después
        observations=order_data.observations,
    )

    db.add(new_order)
    db.flush()  # Para obtener el ID del pedido antes de agregar los ítems

    total = 0
    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise ValueError(f"Product with ID {item.product_id} not found")

        subtotal = item.quantity * item.unit_price
        total += subtotal

        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=subtotal,
        )
        db.add(order_item)

    sync = SyncStatus(order_id=new_order.id, platform="cianbox", status="pending")
    db.add(sync)

    new_order.total_amount = total
    db.commit()
    db.refresh(new_order)

    # Llamada a la función de sincronización
    order_sinc_response: SyncStatusResponse = sync_order(new_order)

    db.add(
        SyncStatus(
            order_id=new_order.id,
            platform="cianbox",
            status=order_sinc_response.status,
            synced_at=(
                datetime.now() if order_sinc_response.status == "synced" else None
            ),
            error_message=order_sinc_response.error_message,
        )
    )
    db.commit()

    return new_order


def get_all_orders() -> list[Order]:
    return db.query(Order).all()


def get_order(order_id: int, user: User):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise NotFoundException(f"Order with ID {order_id} not found")

    # Solo admins o el mismo usuario pueden ver
    if order.user_id != user.id and user.role not in [
        RoleEnum.ADMIN,
        RoleEnum.OWNER,
    ]:
        raise UnauthorizedException("You do not have permission to view this order")

    return order


def get_order_by_user_id(user_id: int) -> list[Order]:
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    if not orders:
        raise NotFoundException(f"No orders found for user ID {user_id}")
    return orders


def sync_order_with_cianbox(order_id: int):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise NotFoundException(f"Order with ID {order_id} not found")

    sync_status = next(
        (s for s in order.sync_statuses if s.platform == "cianbox"), None
    )

    if not sync_status:
        raise BadRequestException(
            f"No synchronization status found for order ID {order_id} on Cianbox"
        )

    if sync_status.status == "success":
        raise BadRequestException(
            f"Order ID {order_id} has already been synchronized with Cianbox"
        )

    try:
        # Lógica para transformar y enviar a Cianbox (aquí llamás a tu adaptador)
        # payload = transform_order_to_cianbox(order)
        payload = order
        sync_order(payload)  # Este sería tu cliente HTTP

        sync_status.status = "success"
        sync_status.error_message = "Synchronized successfully"
        sync_status.synced_at = datetime.now()
    except Exception as e:
        sync_status.status = "failed"
        sync_status.error_message = str(e)
        sync_status.synced_at = datetime.now()

    db.commit()
    return sync_status
