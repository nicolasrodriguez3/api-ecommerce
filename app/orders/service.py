from sqlalchemy.orm import Session
from app.orders.models import Order, OrderItem
from app.orders.schemas import OrderCreate
from app.products.models import Product
from app.users.models import User

def create_order(db: Session, order_data: OrderCreate, user_id: int) -> Order:
    new_order = Order(
        user_id=user_id,
        synced_with_cianbox=False,
        total_amount=0.0,  # Inicialmente 0, se actualizará después
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

    new_order.total_amount = total
    db.commit()
    db.refresh(new_order)
    return new_order
