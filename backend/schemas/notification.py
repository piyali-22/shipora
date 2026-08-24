from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationPublic(BaseModel):
    id: str
    order_id: Optional[str] = None
    tracking_id: Optional[str] = None
    title: str
    message: str
    is_read: bool
    created_at: datetime
