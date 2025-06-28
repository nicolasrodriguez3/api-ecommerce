from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import and_, desc, asc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.order import (
    Order,
    OrderItem,
    OrderAddress,
    Payment,
    OrderStatusHistory,
    OrderStatus,
)
from app.schemas.order import OrderFilters


class OrderRepository(BaseRepository[Order]):
    """Repository for Order operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Order)

    async def create_order_with_items(
        self,
        order_data: dict,
        items_data: List[dict],
        shipping_address_data: dict,
        billing_address_data: Optional[dict] = None,
        payment_data: Optional[dict] = None,
    ) -> Order:
        """Create an order with all related data in a single transaction."""

        # Crear la orden principal
        order = Order(**order_data)
        self.db.add(order)
        await self.db.flush()  # Para obtener el ID

        # Crear items
        for item_data in items_data:
            item_data["order_id"] = order.id
            order_item = OrderItem(**item_data)
            self.db.add(order_item)

        # Crear dirección de envío
        shipping_address_data.update({"order_id": order.id, "address_type": "shipping"})
        shipping_address = OrderAddress(**shipping_address_data)
        self.db.add(shipping_address)

        # Crear dirección de facturación si se proporciona
        if billing_address_data:
            billing_address_data.update(
                {"order_id": order.id, "address_type": "billing"}
            )
            billing_address = OrderAddress(**billing_address_data)
            self.db.add(billing_address)

        # Crear pago si se proporciona
        if payment_data:
            payment_data["order_id"] = order.id
            payment = Payment(**payment_data)
            self.db.add(payment)

        # Crear historial de estado inicial
        status_history = OrderStatusHistory(
            order_id=order.id,
            previous_status=None,
            new_status=order.status,
            notes="Order created",
        )
        self.db.add(status_history)

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_order_with_details(self, order_id: int) -> Optional[Order]:
        """Get order with all related data."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.shipping_address),
                selectinload(Order.billing_address),
                selectinload(Order.payments),
                selectinload(Order.status_history),
            )
            .where(Order.id == order_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_orders_by_user(
        self,
        user_id: int,
        status: Optional[OrderStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Order], int]:
        """Get orders for a specific user with pagination."""
        # Contar total
        count_stmt = select(func.count(Order.id)).where(Order.user_id == user_id)
        if status:
            count_stmt = count_stmt.where(Order.status == status)

        count_result = await self.db.execute(count_stmt)
        count_result = count_result.scalar()
        total = count_result if count_result is not None else 0

        # Obtener órdenes
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(desc(Order.created_at))
            .offset(offset)
            .limit(limit)
        )

        if status:
            stmt = stmt.where(Order.status == status)

        result = await self.db.execute(stmt)
        orders = result.scalars().all()

        return list(orders), total

    async def get_orders_with_filters(
        self, filters: OrderFilters
    ) -> Tuple[List[Order], int]:
        """Get orders with complex filtering and pagination."""
        stmt = select(Order)

        # Aplicar filtros
        conditions = []

        if filters.status:
            conditions.append(Order.status == filters.status)

        if filters.user_id:
            conditions.append(Order.user_id == filters.user_id)

        if filters.date_from:
            conditions.append(Order.created_at >= filters.date_from)

        if filters.date_to:
            conditions.append(Order.created_at <= filters.date_to)

        if filters.min_amount:
            conditions.append(Order.total_amount >= filters.min_amount)

        if filters.max_amount:
            conditions.append(Order.total_amount <= filters.max_amount)

        if filters.order_number:
            conditions.append(Order.order_number.ilike(f"%{filters.order_number}%"))

        if filters.synced_with_erp is not None:
            conditions.append(Order.synced_with_erp == filters.synced_with_erp)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Contar total antes de paginación
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()
        total = total if total is not None else 0

        # Aplicar ordenamiento
        if filters.sort_order.lower() == "desc":
            stmt = stmt.order_by(desc(getattr(Order, filters.sort_by)))
        else:
            stmt = stmt.order_by(asc(getattr(Order, filters.sort_by)))

        # Aplicar paginación
        offset = (filters.page - 1) * filters.page_size
        stmt = stmt.offset(offset).limit(filters.page_size)

        result = await self.db.execute(stmt)
        orders = result.scalars().all()

        return list(orders), total

    async def update_order_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        user_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Optional[Order]:
        """Update order status and create history entry."""
        order = await self.get_by_id(order_id)
        if not order:
            return None

        previous_status = order.status
        order.status = new_status

        # Actualizar fechas específicas según el estado
        now = datetime.utcnow()
        if new_status == OrderStatus.SHIPPED:
            order.shipped_at = now
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_at = now

        # Crear entrada en el historial
        status_history = OrderStatusHistory(
            order_id=order_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by_user_id=user_id,
            notes=notes,
        )
        self.db.add(status_history)

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.shipping_address),
                selectinload(Order.billing_address),
                selectinload(Order.payments),
            )
            .where(Order.order_number == order_number)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_orders_by_status(self, status: OrderStatus) -> Tuple[List[Order], int]:
        """Get all orders with specific status."""
        stmt = (
            select(Order).where(Order.status == status).order_by(desc(Order.created_at))
        )
        result = await self.db.execute(stmt)
        
        # Contar total antes de paginación
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()
        total = total if total is not None else 0
        
        return list(result.scalars().all()), total

    async def get_orders_stats(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> dict:
        """Get order statistics."""
        conditions = []

        if date_from:
            conditions.append(Order.created_at >= date_from)
        if date_to:
            conditions.append(Order.created_at <= date_to)

        base_condition = and_(*conditions) if conditions else True

        # Estadísticas básicas
        count_stmt = select(func.count(Order.id))

        if conditions:
            count_stmt.where(and_(*conditions))

        count_result = await self.db.execute(count_stmt)
        total_orders = count_result.scalar()

        # Estadísticas por estado
        status_stmt = select(Order.status, func.count(Order.id))

        if conditions:
            status_stmt.where(and_(*conditions)).group_by(Order.status)
        else:
            status_stmt.group_by(Order.status)

        status_result = await self.db.execute(status_stmt)
        status_stats = status_result.all()

        # Estadísticas financieras
        financial_conditions = [base_condition, Order.status != OrderStatus.CANCELLED]
        financial_stmt = select(
            func.sum(Order.total_amount), func.avg(Order.total_amount)
        ).where(and_(*financial_conditions))
        financial_result = await self.db.execute(financial_stmt)
        financial_stats = financial_result.first()

        total_revenue = float(financial_stats[0]) if financial_stats and financial_stats[0] is not None else 0.0
        average_order_value = float(financial_stats[1]) if financial_stats and financial_stats[1] is not None else 0.0

        result = {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "average_order_value": average_order_value,
        }

        # Agregar estadísticas por estado
        for status, count in status_stats:
            result[f"{status.value}_orders"] = count

        return result

    async def search_orders(self, search_term: str, limit: int = 20) -> List[Order]:
        """Search orders by order number, user email, or product name."""
        stmt = (
            select(Order)
            .join(Order.user)
            .join(Order.items)
            .where(
                or_(
                    Order.order_number.ilike(f"%{search_term}%"),
                    Order.user.has(email=search_term),
                    Order.items.any(OrderItem.product_name.ilike(f"%{search_term}%")),
                )
            )
            .options(selectinload(Order.items))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def bulk_update_status(
        self,
        order_ids: List[int],
        new_status: OrderStatus,
        user_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> int:
        """Bulk update order status."""
        stmt = select(Order).where(Order.id.in_(order_ids))
        result = await self.db.execute(stmt)
        orders = result.scalars().all()

        updated_count = 0

        for order in orders:
            if order.status != new_status:
                previous_status = order.status
                order.status = new_status

                # Crear entrada en el historial
                status_history = OrderStatusHistory(
                    order_id=order.id,
                    previous_status=previous_status,
                    new_status=new_status,
                    changed_by_user_id=user_id,
                    notes=notes,
                )
                self.db.add(status_history)
                updated_count += 1

        await self.db.commit()
        return updated_count

    async def get_orders_for_sync(self, limit: int = 100) -> List[Order]:
        """Get orders that need to be synced with ERP."""
        stmt = (
            select(Order)
            .where(Order.synced_with_erp == False)
            .where(
                Order.status.in_(
                    [
                        OrderStatus.CONFIRMED,
                        OrderStatus.PROCESSING,
                        OrderStatus.SHIPPED,
                        OrderStatus.DELIVERED,
                    ]
                )
            )
            .options(selectinload(Order.items))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_synced(
        self, order_id: int, cianbox_order_id: str
    ) -> Optional[Order]:
        """Mark order as synced with ERP."""
        order = await self.get_by_id(order_id)
        if order:
            order.synced_with_erp = True
            order.cianbox_order_id = cianbox_order_id
            await self.db.commit()
            await self.db.refresh(order)
        return order


class OrderItemRepository(BaseRepository[OrderItem]):
    """Repository for OrderItem operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, OrderItem)

    async def get_items_by_order(self, order_id: int) -> List[OrderItem]:
        """Get all items for a specific order."""
        stmt = select(OrderItem).where(OrderItem.order_id == order_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_items_by_product(self, product_id: int) -> List[OrderItem]:
        """Get all order items for a specific product."""
        stmt = select(OrderItem).where(OrderItem.product_id == product_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Payment)

    async def get_payments_by_order(self, order_id: int) -> List[Payment]:
        """Get all payments for a specific order."""
        stmt = (
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(desc(Payment.created_at))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_payment_by_transaction_id(
        self, transaction_id: str
    ) -> Optional[Payment]:
        """Get payment by transaction ID."""
        stmt = select(Payment).where(Payment.transaction_id == transaction_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
