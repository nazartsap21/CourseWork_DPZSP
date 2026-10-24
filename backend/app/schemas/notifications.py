from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..models import NotificationType


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: NotificationType
    message: str
    order_id: int | None
    is_read: bool
    created_at: datetime


class InboxOut(BaseModel):
    items: list[NotificationOut]
    unread_count: int
