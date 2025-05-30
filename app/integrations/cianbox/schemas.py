from pydantic import BaseModel


class SyncResponse(BaseModel):
    status: str
    message: str | None = None


class SyncStatusResponse(BaseModel):
    order_id: int
    platform: str
    status: str
    synced_at: str | None = None
    error_message: str | None = None
