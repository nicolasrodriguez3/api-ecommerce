from typing import List
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.exceptions import NotFoundException
from app.products.models import Product
from app.products.schemas import ProductCreate


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    order_by: str = "id",
    order_dir: str = "asc",
) -> tuple[List[Product], int]:
    query = db.query(Product)

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    # Verificar que el campo sea válido
    if hasattr(Product, order_by):
        column = getattr(Product, order_by)
        if order_dir.lower() == "desc":
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))

    total: int = query.count()
    products: List[Product] = query.offset(skip).limit(limit).all()
    return products, total


def get_by_id(db: Session, product_id: int) -> Product:
    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        raise NotFoundException(f"Product with ID {product_id} not found")
    return product


def create(product_data: ProductCreate, db: Session):
    new_product = Product(**product_data.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


def update(product_id: int, product_data: ProductCreate, db: Session):
    product = get_by_id(product_id, db)
    for key, value in product_data.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete(product_id: int, db: Session):
    product = get_by_id(product_id, db)
    db.delete(product)
    db.commit()
