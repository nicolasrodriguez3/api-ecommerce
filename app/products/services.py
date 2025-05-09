from sqlalchemy.orm import Session
from fastapi import HTTPException
from . import models, schemas


def get_all(db: Session):
    return db.query(models.Product).all()


def get_by_id(product_id: int, db: Session):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


def create(product_data: schemas.ProductCreate, db: Session):
    new_product = models.Product(**product_data.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


def update(product_id: int, product_data: schemas.ProductCreate, db: Session):
    product = get_by_id(product_id, db)
    for key, value in product_data.dict().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete(product_id: int, db: Session):
    product = get_by_id(product_id, db)
    db.delete(product)
    db.commit()
