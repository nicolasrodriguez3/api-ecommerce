from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from . import schemas, services
from app.core.database import get_db

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=list[schemas.ProductRead])
def list_products(db: Session = Depends(get_db)):
    return services.get_all(db)

@router.get("/{product_id}", response_model=schemas.ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return services.get_by_id(product_id, db)

@router.post("/", response_model=schemas.ProductRead, status_code=201)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return services.create(product, db)

@router.put("/{product_id}", response_model=schemas.ProductRead)
def update_product(product_id: int, updated_data: schemas.ProductCreate, db: Session = Depends(get_db)):
    return services.update(product_id, updated_data, db)

@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    services.delete(product_id, db)
