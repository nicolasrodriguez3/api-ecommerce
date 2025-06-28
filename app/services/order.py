from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.repositories.order import (
    OrderRepository,
    OrderItemRepository,
    PaymentRepository,
)
from app.models.order import Order, OrderStatus, PaymentStatus, PaymentMethod
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderResponse,
    OrderItemCreate,
    PaymentCreate,
    OrderFilters,
    OrderStats
)
from app.core.exceptions import NotFoundError, BusinessLogicError
from app.core.logger import setup_logger

# from app.services.inventory import InventoryService
# from app.services.notifications import NotificationService
from app.utils.order_number import generate_order_number

logger = setup_logger(__name__)


class OrderService:
    """Service layer for order operations."""

    def __init__(
        self,
        db: AsyncSession,
        # inventory_service: Optional[InventoryService] = None,
        # notification_service: Optional[NotificationService] = None
    ):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.order_item_repo = OrderItemRepository(db)
        self.payment_repo = PaymentRepository(db)
        # self.inventory_service = inventory_service
        # self.notification_service = notification_service

    async def create_order(
        self, order_data: OrderCreate, user_id: int
    ) -> OrderResponse:
        """Create a new order with items and addresses."""
        try:
            # Validar stock disponible
            # if self.inventory_service:
            #     await self._validate_inventory(order_data.items)

            # Generar número de orden único
            order_number = await self._generate_unique_order_number()

            # Calcular totales
            subtotal, total_amount = await self._calculate_order_totals(order_data)

            # Preparar datos de la orden
            order_dict = {
                "order_number": order_number,
                "user_id": user_id,
                "status": OrderStatus.PENDING,
                "subtotal": subtotal,
                "tax_amount": order_data.tax_amount or 0.0,
                "shipping_cost": order_data.shipping_cost or 0.0,
                "discount_amount": order_data.discount_amount or 0.0,
                "total_amount": total_amount,
                "notes": order_data.notes,
                # "estimated_delivery_date": order_data.estimated_delivery_date
            }

            # Preparar items
            items_data = []
            for item in order_data.items:
                item_dict = {
                    "product_id": item.product_id,
                    # "product_name": item.product_name,
                    # "product_sku": item.product_sku,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.quantity * item.unit_price,
                    # "product_metadata": item.product_metadata
                }
                items_data.append(item_dict)

            # Preparar dirección de envío
            shipping_address_data = order_data.shipping_address.model_dump()

            # Preparar dirección de facturación si existe
            billing_address_data = None
            if order_data.billing_address:
                billing_address_data = order_data.billing_address.model_dump()

            # Crear orden completa
            order = await self.order_repo.create_order_with_items(
                order_data=order_dict,
                items_data=items_data,
                shipping_address_data=shipping_address_data,
                billing_address_data=billing_address_data,
            )

            # Reservar stock
            # if self.inventory_service:
            #     await self._reserve_inventory(order.items)

            # Enviar notificación
            # if self.notification_service:
            #     await self.notification_service.send_order_created_notification(order)

            logger.info(f"Order created successfully: {order.order_number}")
            return OrderResponse.model_validate(order)

        except SQLAlchemyError as e:
            logger.error(f"Database error creating order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating order",
            )
        except Exception as e:
            logger.error(f"Unexpected error creating order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error occurred",
            )

    async def get_order_by_id(
        self, order_id: int, user_id: Optional[int] = None
    ) -> OrderResponse:
        """Get order by ID with full details."""
        order = await self.order_repo.get_order_with_details(order_id)

        if not order:
            raise NotFoundError("Order", order_id)

        # Verificar que el usuario tenga acceso a la orden
        if user_id and order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this order",
            )

        return OrderResponse.model_validate(order)

    async def get_order_by_number(
        self, order_number: str, user_id: Optional[int] = None
    ) -> OrderResponse:
        """Get order by order number."""
        order = await self.order_repo.get_order_by_number(order_number)

        if not order:
            raise NotFoundError("Order", order_number)

        if user_id and order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this order",
            )

        return OrderResponse.model_validate(order)

    async def get_user_orders(
        self,
        user_id: int,
        status: Optional[OrderStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[OrderResponse], int]:
        """Get orders for a specific user."""
        offset = (page - 1) * page_size
        orders, total = await self.order_repo.get_orders_by_user(
            user_id=user_id, status=status, limit=page_size, offset=offset
        )

        order_responses = [OrderResponse.model_validate(order) for order in orders]
        return order_responses, total

    async def get_orders_with_filters(
        self, filters: OrderFilters
    ) -> Tuple[List[OrderResponse], int]:
        """Get orders with complex filtering."""
        orders, total = await self.order_repo.get_orders_with_filters(filters)
        order_responses = [OrderResponse.model_validate(order) for order in orders]
        return order_responses, total
    
    async def get_orders_by_status(
        self,
        status: OrderStatus,
    ) -> Tuple[List[OrderResponse], int]:
        """Get orders filtered by status."""
        orders, total = await self.order_repo.get_orders_by_status(status)
        
        order_responses = [OrderResponse.model_validate(order) for order in orders]
        return order_responses, total

    async def update_order_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        user_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> OrderResponse:
        """Update order status with validation."""
        order = await self.order_repo.get_by_id(order_id)

        if not order:
            raise NotFoundError("Order", order_id)

        # Validar transición de estado
        await self._validate_status_transition(order.status, new_status)

        # Actualizar estado
        updated_order = await self.order_repo.update_order_status(
            order_id=order_id, new_status=new_status, user_id=user_id, notes=notes
        )
        if not updated_order:
            raise NotFoundError("Order", order_id)

        # Procesar acciones adicionales según el nuevo estado
        await self._handle_status_change_actions(updated_order, new_status)

        # Enviar notificación
        # if self.notification_service:
        #     await self.notification_service.send_status_change_notification(updated_order)

        logger.info(f"Order {order.order_number} status updated to {new_status}")
        return OrderResponse.model_validate(updated_order)

    async def cancel_order(
        self, order_id: int, user_id: Optional[int] = None, reason: Optional[str] = None
    ) -> OrderResponse:
        """Cancel an order."""
        order = await self.order_repo.get_by_id(order_id)

        if not order:
            raise NotFoundError("Order", order_id)

        if not order.is_cancellable():
            raise BusinessLogicError("Order cannot be cancelled in current status")

        # Cancelar orden
        updated_order = await self.order_repo.update_order_status(
            order_id=order_id,
            new_status=OrderStatus.CANCELLED,
            user_id=user_id,
            notes=f"Order cancelled. Reason: {reason}" if reason else "Order cancelled",
        )

        # Liberar stock reservado
        # if self.inventory_service:
        #     await self._release_inventory(order.items)

        # Procesar reembolso si hay pagos
        await self._process_cancellation_refund(order)

        logger.info(f"Order {order.order_number} cancelled successfully")
        return OrderResponse.model_validate(updated_order)

    async def add_payment(
        self, order_id: int, payment_data: PaymentCreate
    ) -> OrderResponse:
        """Add a payment to an order."""
        order = await self.order_repo.get_by_id(order_id)

        if not order:
            raise NotFoundError("Order", order_id)

        # Crear pago
        payment_dict = {"order_id": order_id, **payment_data.model_dump()}

        payment = await self.payment_repo.create(payment_dict)

        # Si el pago es exitoso, actualizar estado de la orden
        if payment.payment_status == PaymentStatus.CAPTURED:
            await self._check_and_update_payment_status(order)

        # Obtener orden actualizada con detalles
        updated_order = await self.order_repo.get_order_with_details(order_id)
        return OrderResponse.model_validate(updated_order)

    async def get_order_stats(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> OrderStats:
        """Get order statistics."""
        stats = await self.order_repo.get_orders_stats(date_from, date_to)
        return OrderStats(**stats)

    async def search_orders(
        self, search_term: str, limit: int = 20
    ) -> List[OrderResponse]:
        """Search orders by various criteria."""
        orders = await self.order_repo.search_orders(search_term, limit)
        return [OrderResponse.model_validate(order) for order in orders]

    async def bulk_update_status(
        self,
        order_ids: List[int],
        new_status: OrderStatus,
        user_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> int:
        """Bulk update order status."""
        # Validar que todas las órdenes existan y puedan cambiar de estado
        for order_id in order_ids:
            order = await self.order_repo.get_by_id(order_id)
            if not order:
                raise NotFoundError("Order", order_id)

            await self._validate_status_transition(order.status, new_status)

        # Realizar actualización masiva
        updated_count = await self.order_repo.bulk_update_status(
            order_ids=order_ids, new_status=new_status, user_id=user_id, notes=notes
        )

        logger.info(f"Bulk updated {updated_count} orders to status {new_status}")
        return updated_count

    # Métodos privados auxiliares

    async def _validate_inventory(self, items: List[OrderItemCreate]) -> None:
        """Validate inventory availability for order items."""
        # for item in items:
        #     available = await self.inventory_service.check_availability(
        #         item.product_id, item.quantity
        #     )
        #     if not available:
        #         raise BusinessLogicError(
        #             f"Insufficient stock for product {item.product_name}"
        #         )
        pass

    async def _reserve_inventory(self, items) -> None:
        """Reserve inventory for order items."""
        # for item in items:
        #     await self.inventory_service.reserve_stock(
        #         item.product_id, item.quantity
        #     )
        pass

    async def _release_inventory(self, items) -> None:
        """Release reserved inventory."""
        # for item in items:
        #     await self.inventory_service.release_stock(
        #         item.product_id, item.quantity
        #     )
        pass

    async def _calculate_order_totals(
        self, order_data: OrderCreate
    ) -> Tuple[float, float]:
        """Calculate order subtotal and total amount."""
        subtotal = sum(item.quantity * item.unit_price for item in order_data.items)

        total_amount = (
            subtotal
            + (order_data.tax_amount or 0.0)
            + (order_data.shipping_cost or 0.0)
            - (order_data.discount_amount or 0.0)
        )

        return subtotal, total_amount

    async def _generate_unique_order_number(self) -> str:
        """Generate a unique order number."""
        while True:
            order_number = generate_order_number()
            existing = await self.order_repo.get_order_by_number(order_number)
            if not existing:
                return order_number

    async def _validate_status_transition(
        self, current_status: OrderStatus, new_status: OrderStatus
    ) -> None:
        """Validate if status transition is allowed."""
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PROCESSING: [OrderStatus.READY_TO_SHIP, OrderStatus.CANCELLED],
            OrderStatus.READY_TO_SHIP: [OrderStatus.SHIPPED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [OrderStatus.REFUNDED],
            OrderStatus.CANCELLED: [],
            OrderStatus.REFUNDED: [],
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise BusinessLogicError(
                f"Invalid status transition from {current_status} to {new_status}"
            )

    async def _handle_status_change_actions(
        self, order: Order, new_status: OrderStatus
    ) -> None:
        """Handle additional actions when order status changes."""
        if new_status == OrderStatus.CONFIRMED:
            # Confirmar reserva de stock
            # if self.inventory_service:
            #     await self._confirm_inventory_reservation(order.items)
            pass

        elif new_status == OrderStatus.SHIPPED:
            # Generar tracking, enviar notificación de envío, etc.
            pass

        elif new_status == OrderStatus.DELIVERED:
            # Confirmar entrega, actualizar inventario final, etc.
            # if self.inventory_service:
            #     await self._confirm_inventory_consumption(order.items)
            pass

    async def _confirm_inventory_reservation(self, items) -> None:
        """Confirm inventory reservation."""
        # for item in items:
        #     await self.inventory_service.confirm_reservation(
        #         item.product_id, item.quantity
        #     )
        pass

    async def _confirm_inventory_consumption(self, items) -> None:
        """Confirm inventory consumption on delivery."""
        # for item in items:
        #     await self.inventory_service.consume_stock(
        #         item.product_id, item.quantity
        #     )
        pass

    async def _process_cancellation_refund(self, order: Order) -> None:
        """Process refund for cancelled order."""
        # Implementar lógica de reembolso según el gateway de pago
        pass

    async def _check_and_update_payment_status(self, order: Order) -> None:
        """Check if order is fully paid and update status accordingly."""
        payments = await self.payment_repo.get_payments_by_order(order.id)

        total_paid = sum(
            p.amount for p in payments if p.payment_status == PaymentStatus.CAPTURED
        )

        if total_paid >= order.total_amount and order.status == OrderStatus.PENDING:
            await self.order_repo.update_order_status(
                order_id=order.id,
                new_status=OrderStatus.CONFIRMED,
                notes="Payment confirmed",
            )
