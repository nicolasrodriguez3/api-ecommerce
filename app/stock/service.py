from sqlalchemy.orm import Session, joinedload
from app.products.models import Product
from app.core.exceptions import NotFoundException, BadRequestException
from app.stock.models import StockHistory
from app.products.schemas import ProductPublicResponse
from app.core import db_connection

db: Session = db_connection.session

def adjust_stock(product_id: int, quantity: int, reason: str) -> ProductPublicResponse:
    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        raise NotFoundException(f"Product with ID {product_id} not found")

    new_stock = product.stock + quantity
    if new_stock < 0:
        raise BadRequestException("Stock no puede quedar negativo")

    product.stock = new_stock

    history = StockHistory(product_id=product_id, quantity=quantity, reason=reason)
    db.add(history)

    db.commit()
    db.refresh(product)

    product = db.query(Product).options(joinedload(Product.category)).get(product_id)
    return ProductPublicResponse.model_validate(product)
