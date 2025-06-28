from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.order import OrderStatus, PaymentStatus, PaymentMethod


# ==================== ORDER ITEM SCHEMAS ====================

class OrderItemCreate(BaseModel):
    """Schema for creating order items."""
    
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: int = Field(..., gt=0, le=1000, description="Quantity to order")
    unit_price: float = 0


class OrderItemResponse(BaseModel):
    """Schema for order item response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    product_id: int
    product_name: str
    product_sku: Optional[str] = None
    quantity: int
    unit_price: float
    total_price: float
    product_metadata: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ==================== ORDER ADDRESS SCHEMAS ====================

class OrderAddressCreate(BaseModel):
    """Schema for creating order addresses."""
    
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    address_line_1: str = Field(..., min_length=1, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state_province: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)


class OrderAddressResponse(BaseModel):
    """Schema for order address response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    address_type: str
    first_name: str
    last_name: str
    company: Optional[str] = None
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state_province: str
    postal_code: str
    country: str
    phone: Optional[str] = None
    email: Optional[str] = None


# ==================== PAYMENT SCHEMAS ====================

class PaymentCreate(BaseModel):
    """Schema for creating payments."""
    
    payment_method: PaymentMethod
    amount: float = Field(..., gt=0)
    currency: str = Field(default="ARS", max_length=3)
    transaction_id: Optional[str] = Field(None, max_length=255)
    gateway_payment_id: Optional[str] = Field(None, max_length=255)


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    amount: float
    currency: str
    transaction_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    failure_reason: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime


# ==================== ORDER STATUS HISTORY SCHEMAS ====================

class OrderStatusHistoryResponse(BaseModel):
    """Schema for order status history response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    previous_status: Optional[OrderStatus] = None
    new_status: OrderStatus
    changed_by_user_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime


# ==================== ORDER SCHEMAS ====================

class OrderCreate(BaseModel):
    """Schema for creating orders."""
    
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Order items")
    shipping_address: OrderAddressCreate = Field(..., description="Shipping address")
    billing_address: Optional[OrderAddressCreate] = Field(None, description="Billing address (optional)")
    notes: Optional[str] = Field(None, max_length=1000, description="Order notes")
    shipping_cost: float = Field(default=0.0, ge=0, description="Shipping cost")
    tax_amount: float = Field(default=0.0, ge=0, description="Tax amount")
    discount_amount: float = Field(default=0.0, ge=0, description="Discount amount")
    payment: Optional[PaymentCreate] = Field(None, description="Payment information")


class OrderResponse(BaseModel):
    """Schema for order response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    order_number: str
    user_id: int
    status: OrderStatus
    subtotal: float
    tax_amount: float
    shipping_cost: float
    discount_amount: float
    total_amount: float
    notes: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cianbox_order_id: Optional[str] = None
    synced_with_erp: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Relaciones
    items: List[OrderItemResponse]
    shipping_address: Optional[OrderAddressResponse] = None
    billing_address: Optional[OrderAddressResponse] = None
    payments: List[PaymentResponse] = []
    status_history: List[OrderStatusHistoryResponse] = []


class OrderSummaryResponse(BaseModel):
    """Schema for order summary (list view)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    order_number: str
    status: OrderStatus
    total_amount: float
    created_at: datetime
    estimated_delivery_date: Optional[datetime] = None
    total_items: int
    user_id: int


class OrderUpdate(BaseModel):
    """Schema for updating orders."""
    
    notes: Optional[str] = Field(None, max_length=1000)
    internal_notes: Optional[str] = Field(None, max_length=1000)
    estimated_delivery_date: Optional[datetime] = None
    shipping_cost: Optional[float] = Field(None, ge=0)
    tax_amount: Optional[float] = Field(None, ge=0)
    discount_amount: Optional[float] = Field(None, ge=0)


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status."""
    
    status: OrderStatus
    notes: Optional[str] = Field(None, max_length=500, description="Notes about the status change")


class OrderStats(BaseModel):
    total_orders: int
    total_revenue: int
    average_order_value: int

# ==================== ORDER FILTERS ====================

class OrderFilters(BaseModel):
    """Schema for order filtering."""
    
    status: Optional[OrderStatus] = None
    user_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    order_number: Optional[str] = None
    synced_with_erp: Optional[bool] = None
    
    # Paginación
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    # Ordenamiento
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


# ==================== RESPONSE WRAPPERS ====================

class OrderListResponse(BaseModel):
    """Schema for paginated order list response."""
    
    orders: List[OrderSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class OrderStatsResponse(BaseModel):
    """Schema for order statistics."""
    
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    processing_orders: int
    shipped_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_revenue: float
    average_order_value: float


# ==================== BULK OPERATIONS ====================

class BulkOrderStatusUpdate(BaseModel):
    """Schema for bulk status updates."""
    
    order_ids: List[int] = Field(..., min_length=1, max_length=100)
    status: OrderStatus
    notes: Optional[str] = Field(None, max_length=500)


class OrderExportRequest(BaseModel):
    """Schema for order export requests."""
    
    filters: Optional[OrderFilters] = None
    format: str = Field(default="csv", pattern="^(csv|xlsx|pdf)$")
    include_items: bool = Field(default=True)
    include_addresses: bool = Field(default=True)
    include_payments: bool = Field(default=False)