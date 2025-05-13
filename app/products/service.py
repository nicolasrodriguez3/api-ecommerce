from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.products.models import Product
from app.products.schemas import ProductCreate


def get_products(
    db: Session, skip: int = 0, limit: int = 10, search: str | None = None
) -> tuple[List[Product], int]:
    query = db.query(Product)

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    total = query.count()
    products = query.offset(skip).limit(limit).all()
    return products, total


def get_by_id(product_id: int, db: Session) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
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
