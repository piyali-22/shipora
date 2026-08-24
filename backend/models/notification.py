"""
In-app notification document model.

One document per notification per recipient. Kept simple and
denormalized (tracking_id stored directly) so the notification center
UI can render a list without needing to join back to orders.
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class NotificationInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    recipient_id: str
    order_id: Optional[str] = None
    tracking_id: Optional[str] = None
    title: str
    message: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
