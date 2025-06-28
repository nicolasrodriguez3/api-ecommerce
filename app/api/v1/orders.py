from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from fastapi.security import HTTPBearer

from app.api.dependencies import get_order_service
from app.auth.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.order import OrderStatus
from app.services.order import OrderService

# from app.services.inventory import InventoryService
# from app.services.notifications import NotificationService
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    PaymentCreate,
    OrderFilters,
    OrderStats,
)
from app.schemas.common import PaginatedResponse


router = APIRouter(prefix="/orders", tags=["Orders"])


# Endpoints públicos (requieren autenticación de usuario)
@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Create a new order.

    - **order_data**: Order information including items and addresses
    - Returns the created order
    """
    return await order_service.create_order(order_data, current_user.id)


@router.get("/me", response_model=PaginatedResponse[OrderResponse])
async def get_my_orders(
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Get current user's orders with pagination.

    - **status**: Optional status filter
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    """
    orders, total = await order_service.get_user_orders(
        user_id=current_user.id, status=status, page=page, page_size=page_size
    )

    return PaginatedResponse(items=orders, total=total, page=page, page_size=page_size)


@router.get("/me/{order_id}", response_model=OrderResponse)
async def get_my_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Get a specific order belonging to the current user.

    - **order_id**: Order ID
    """
    return await order_service.get_order_by_id(order_id, current_user.id)


@router.get("/me/number/{order_number}", response_model=OrderResponse)
async def get_my_order_by_number(
    order_number: str,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Get an order by order number for the current user.

    - **order_number**: Order number
    """
    return await order_service.get_order_by_number(order_number, current_user.id)


@router.post("/me/{order_id}/cancel", response_model=OrderResponse)
async def cancel_my_order(
    order_id: int,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Cancel an order belonging to the current user.

    - **order_id**: Order ID
    - **reason**: Optional cancellation reason
    """
    return await order_service.cancel_order(order_id, current_user.id, reason)


@router.post("/{order_id}/payments", response_model=OrderResponse)
async def add_payment_to_order(
    order_id: int,
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Add a payment to an order.

    - **order_id**: Order ID
    - **payment_data**: Payment information
    """
    # Verificar que la orden pertenece al usuario actual
    await order_service.get_order_by_id(order_id, current_user.id)
    return await order_service.add_payment(order_id, payment_data)


# Endpoints administrativos


@router.get("/", response_model=PaginatedResponse[OrderResponse])
async def get_all_orders(
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    min_amount: Optional[float] = Query(None, description="Minimum order amount"),
    max_amount: Optional[float] = Query(None, description="Maximum order amount"),
    order_number: Optional[str] = Query(None, description="Filter by order number"),
    synced_with_erp: Optional[bool] = Query(
        None, description="Filter by ERP sync status"
    ),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_admin: User = Depends(require_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Get all orders with advanced filtering (Admin only).

    Multiple filter options available for comprehensive order management.
    """
    filters = OrderFilters(
        status=status,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        order_number=order_number,
        synced_with_erp=synced_with_erp,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    orders, total = await order_service.get_orders_with_filters(filters)

    return PaginatedResponse(
        data=orders,
        total_elements=total,
        current_page=page,
        total_pages=1234
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: int,
    current_admin: User = Depends(require_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Get order by ID (Admin only).

    - **order_id**: Order ID
    """
    return await order_service.get_order_by_id(order_id)


@router.get("/number/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str,
    current_admin: User = Depends(require_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Get order by order number (Admin only).

    - **order_number**: Order number
    """
    return await order_service.get_order_by_number(order_number)


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    new_status: OrderStatus,
    notes: Optional[str] = Query(None, description="Status change notes"),
    current_admin: User = Depends(require_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Update order status (Admin only).

    - **order_id**: Order ID
    - **new_status**: New order status
    - **notes**: Optional notes for the status change
    """
    return await order_service.update_order_status(
        order_id=order_id, new_status=new_status, user_id=current_admin.id, notes=notes
    )


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    current_admin: User = Depends(require_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Cancel an order (Admin only).

    - **order_id**: Order ID
    - **reason**: Optional cancellation reason
    """
    return await order_service.cancel_order(order_id, current_admin.id, reason)


@router.get("/search/", response_model=List[OrderResponse])
async def search_orders(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_admin: User = Depends(require_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Search orders by order number, user email, or product name (Admin only).

    - **q**: Search term (minimum 2 characters)
    - **limit**: Maximum number of results
    """
    return await order_service.search_orders(q, limit)


@router.get("/stats/overview", response_model=OrderStats)
async def get_order_statistics(
    date_from: Optional[datetime] = Query(None, description="Statistics from date"),
    date_to: Optional[datetime] = Query(None, description="Statistics to date"),
    current_admin: User = Depends(require_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Get order statistics and metrics (Admin only).

    - **date_from**: Optional start date for statistics
    - **date_to**: Optional end date for statistics
    """
    return await order_service.get_order_stats(date_from, date_to)


# @router.patch("/bulk/status", response_model=MessageResponse)
# async def bulk_update_order_status(
#     bulk_update: BulkStatusUpdate,
#     current_admin: User = Depends(require_admin),
#     order_service: OrderService = Depends(get_order_service)
# ):
#     """
#     Bulk update order status (Admin only).

#     - **bulk_update**: Bulk update data including order IDs and new status
#     """
#     updated_count = await order_service.bulk_update_status(
#         order_ids=bulk_update.order_ids,
#         new_status=bulk_update.new_status,
#         user_id=current_admin.id,
#         notes=bulk_update.notes
#     )

#     return MessageResponse(
#         message=f"Successfully updated {updated_count} orders to status {bulk_update.new_status}"
#     )


@router.get("/status/{status}", response_model=List[OrderResponse])
async def get_orders_by_status(
    status: OrderStatus,
    current_admin: User = Depends(require_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Get all orders with specific status (Admin only).

    - **status**: Order status to filter by
    """
    orders = await order_service.get_orders_by_status(status)
    return [OrderResponse.model_validate(order) for order in orders]


# Endpoints específicos para integración ERP


@router.get("/sync/pending", response_model=List[OrderResponse])
async def get_orders_pending_sync(
    limit: int = Query(100, ge=1, le=1000, description="Maximum orders to return"),
    current_admin: User = Depends(require_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Get orders that need to be synced with ERP (Admin only).

    - **limit**: Maximum number of orders to return
    """
    orders = await order_service.order_repo.get_orders_for_sync(limit)
    return [OrderResponse.model_validate(order) for order in orders]


# @router.patch("/{order_id}/sync", response_model=OrderResponse)
# async def mark_order
