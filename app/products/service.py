from typing import List
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from app.categories.models import Category
from app.core.exceptions import BadRequestException, NotFoundException
from app.products.models import Product
from app.products.schemas import ProductCreate
from app.products.schemas import ProductResponse

def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    order_by: str = "id",
    order_dir: str = "asc",
) -> tuple[List[ProductResponse], int]:
    query = db.query(Product).filter(Product.is_active.is_(True)).options(joinedload(Product.category))

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    ALLOWED_ORDER_FIELDS = {"id", "name", "price", "stock", "created_at"}
    if order_by not in ALLOWED_ORDER_FIELDS:
        raise BadRequestException(
            f"Invalid order_by field. Allowed fields are: {', '.join(ALLOWED_ORDER_FIELDS)}"
        )

    column = getattr(Product, order_by)
    query = query.order_by(desc(column) if order_dir.lower() == "desc" else asc(column))

    total: int = query.count()
    products: List[Product] = query.offset(skip).limit(limit).all()
    
    result = [ProductResponse.model_validate(p) for p in products]
    return result, total


def get_by_id(db: Session, product_id: int) -> ProductResponse:
    product = _get_one_product(db, product_id)
    
    return ProductResponse.model_validate(product)


def create(product_data: ProductCreate, db: Session) -> ProductResponse:
    _get_category_or_400(db, product_data.category_id)

    new_product = Product(**product_data.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    product_with_category = db.query(Product).options(joinedload(Product.category)).get(new_product.id)
    
    return ProductResponse.model_validate(product_with_category)


def update(product_id: int, product_data: ProductCreate, db: Session) -> ProductResponse:
    product = _get_one_product(db, product_id)

    # Validar categoría
    _get_category_or_400(db, product_data.category_id)

    for key, value in product_data.model_dump().items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    
    product_with_category = db.query(Product).options(joinedload(Product.category)).get(product.id)

    return ProductResponse.model_validate(product_with_category)


def delete(product_id: int, db: Session) -> None:
    product = _get_one_product(db, product_id)
    
    product.is_active = False
    db.commit()


def _get_category_or_400(db: Session, category_id: int) -> Category:
    category = db.query(Category).filter_by(id=category_id).first()
    if not category:
        raise BadRequestException(f"Category with ID {category_id} does not exist")
    return category

def _get_one_product(db: Session, product_id: int) -> Product:
    product = db.query(Product).filter_by(id=product_id, is_active=True).first()
    if not product:
        raise NotFoundException(f"Product with ID {product_id} not found")
    return product