from pydantic import BaseModel, Field


class StockMovementCreate(BaseModel):
    quantity: int = Field(..., description="Cantidad positiva o negativa")
    reason: str = Field(..., description="Motivo del movimiento")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"quantity": 5, "reason": "Compra"},
                {"quantity": -2, "reason": "Venta"},
            ]
        }
    }