from app.integrations.cianbox.schemas import SyncResponse, SyncStatusResponse
from app.orders.models import Order
from datetime import datetime


def sync_order(order: Order) -> SyncStatusResponse:
    try:
        # 1. Preparar los datos a enviar (esto lo veremos más adelante)
        # data = transform_order_to_cianbox_format(order)

        # 2. Enviar los datos a la API externa
        # response = send_to_cianbox_api(data)
        response = SyncResponse.model_validate(
            {
                "status_code": 200,  # Simulando una respuesta exitosa
                "text": "Order synced successfully",
            }
        )

        status_code = getattr(response, "status_code", None)
        if status_code == 200:
            status = "synced"
            error_message = None
        else:
            status = "error"
            error_message = f"Error {status_code}: {getattr(response, 'text', '')}"

    except Exception as e:
        status = "error"
        error_message = str(e)

    return SyncStatusResponse.model_validate(
        {
            "order_id": order.id,
            "platform": "cianbox",
            "status": status,
            "synced_at": datetime.now() if status == "synced" else None,
            "error_message": error_message,
        }
    )
