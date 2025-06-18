from pydantic import BaseModel, field_validator
from datetime import datetime, timezone, timedelta

GMT_MINUS_3 = timezone(timedelta(hours=-3))
DATETIME_FORMAT = "%d-%m-%Y %H:%M:%S"


class BaseResponseModel(BaseModel):
    @field_validator("created_at", "updated_at", mode="before", check_fields=False)
    @classmethod
    def format_datetime(cls, value: datetime | str | None) -> str | None:
        if not value:
            return None
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(GMT_MINUS_3).strftime(DATETIME_FORMAT)

    model_config = {
        "from_attributes": True,
        "extra": "ignore",
    }
