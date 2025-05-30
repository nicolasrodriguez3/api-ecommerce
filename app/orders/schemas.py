from datetime import datetime
from typing import List
from pydantic import BaseModel, field_validator


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

    @field_validator("quantity")
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than zero")
        return v


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    observations: str | None = None


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    total_price: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    model_config = {"from_attributes": True}
