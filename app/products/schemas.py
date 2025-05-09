from datetime import datetime
from pydantic import BaseModel


# Este se usa para crear o actualizar un producto
class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    stock: int = 0


# Este se usa para devolver un producto (incluye el id)
class ProductRead(ProductCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # permite convertir desde un ORM model
