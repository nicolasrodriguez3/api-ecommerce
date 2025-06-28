import enum
from typing import List, Optional
from sqlalchemy import Enum, ForeignKey, String, Text, Float, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.models.base import BaseModel


class OrderStatus(str, enum.Enum):
    """Enumeration for order statuses."""

    PENDING = "pending"  # Orden creada, esperando confirmación
    CONFIRMED = "confirmed"  # Orden confirmada, listo para procesar
    PROCESSING = "processing"  # Preparando productos
    READY_TO_SHIP = "ready_to_ship"  # Listo para enviar
    SHIPPED = "shipped"  # Enviado
    DELIVERED = "delivered"  # Entregado
    CANCELLED = "cancelled"  # Cancelado
    REFUNDED = "refunded"  # Reembolsado


class PaymentStatus(str, enum.Enum):
    """Enumeration for payment statuses."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    """Enumeration for payment methods."""

    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CASH_ON_DELIVERY = "cash_on_delivery"
    DIGITAL_WALLET = "digital_wallet"


class Order(BaseModel):
    """Order model representing customer orders."""

    __tablename__ = "orders"

    # Identificadores
    order_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # Relación con usuario
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    # Status y fechas
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False
    )

    # Importes
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Float, default=0.0)
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)

    # Información adicional
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Fechas importantes
    estimated_delivery_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Integración con ERP
    cianbox_order_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    synced_with_erp: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relaciones
    user: Mapped["User"] = relationship("User", back_populates="orders")  # type: ignore

    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    addresses: Mapped[List["OrderAddress"]] = relationship(
        "OrderAddress",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="order", cascade="all, delete-orphan"
    )

    status_history: Mapped[List["OrderStatusHistory"]] = relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at",
    )

    # Propiedades para acceder a direcciones específicas
    @property
    def shipping_address(self) -> Optional["OrderAddress"]:
        """Get shipping address."""
        return next(
            (addr for addr in self.addresses if addr.address_type == "shipping"), None
        )

    @property
    def billing_address(self) -> Optional["OrderAddress"]:
        """Get billing address."""
        return next(
            (addr for addr in self.addresses if addr.address_type == "billing"), None
        )

    # Métodos
    def calculate_total(self) -> float:
        """Calculate total amount based on subtotal, tax, shipping and discount."""
        return (
            self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        )

    def is_cancellable(self) -> bool:
        """Check if order can be cancelled."""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]

    def is_refundable(self) -> bool:
        """Check if order can be refunded."""
        return self.status in [OrderStatus.DELIVERED, OrderStatus.SHIPPED]

    def get_total_items(self) -> int:
        """Get total number of items in the order."""
        return sum(item.quantity for item in self.items)

    # Métodos para establecer direcciones
    def set_shipping_address(self, address_data: dict) -> "OrderAddress":
        """Set or update shipping address."""
        # Remover dirección de envío existente
        self.addresses = [
            addr for addr in self.addresses if addr.address_type != "shipping"
        ]

        # Crear nueva dirección de envío
        shipping_addr = OrderAddress(**address_data, address_type="shipping")
        self.addresses.append(shipping_addr)
        return shipping_addr

    def set_billing_address(self, address_data: dict) -> "OrderAddress":
        """Set or update billing address."""
        # Remover dirección de facturación existente
        self.addresses = [
            addr for addr in self.addresses if addr.address_type != "billing"
        ]

        # Crear nueva dirección de facturación
        billing_addr = OrderAddress(**address_data, address_type="billing")
        self.addresses.append(billing_addr)
        return billing_addr


class OrderItem(BaseModel):
    """Order item model representing products in an order."""

    __tablename__ = "order_items"

    # Relaciones
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )

    # Información del producto al momento de la compra
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Cantidades y precios
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Metadatos del producto (para preservar información)
    product_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relaciones
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product")  # type: ignore

    def calculate_total_price(self) -> float:
        """Calculate total price for this item."""
        return self.unit_price * self.quantity


class OrderAddress(BaseModel):
    """Order address model for shipping and billing addresses."""

    __tablename__ = "order_addresses"

    # Relación con orden
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False, index=True
    )

    # Tipo de dirección
    address_type: Mapped[str] = mapped_column(
        Enum("shipping", "billing", name="address_type_enum"), nullable=False
    )

    # Información de la dirección
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state_province: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)

    # Información de contacto
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relaciones
    # order: Mapped["Order"] = relationship(
    #     "Order",
    #     overlaps="shipping_address,billing_address"
    # ) usar back_populates en vez de overlaps
    order: Mapped["Order"] = relationship("Order", back_populates="addresses")


class Payment(BaseModel):
    """Payment model for order payments."""

    __tablename__ = "payments"

    # Relación con orden
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False, index=True
    )

    # Información del pago
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod), nullable=False
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING
    )

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="ARS")

    # Identificadores externos
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gateway_payment_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # Información adicional
    gateway_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Fechas
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relaciones
    order: Mapped["Order"] = relationship("Order", back_populates="payments")


class OrderStatusHistory(BaseModel):
    """Order status history model to track status changes."""

    __tablename__ = "order_status_history"

    # Relación con orden
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False, index=True
    )

    # Información del cambio de estado
    previous_status: Mapped[Optional[OrderStatus]] = mapped_column(
        Enum(OrderStatus), nullable=True
    )
    new_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)

    # Usuario que realizó el cambio
    changed_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Notas del cambio
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relaciones
    order: Mapped["Order"] = relationship("Order", back_populates="status_history")
    changed_by: Mapped[Optional["User"]] = relationship("User")  # type: ignore
