from pydantic import BaseModel
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category_id: int
    image_url: str | None = None
    
class ProductRead(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
    category_id: int
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True