"""
Tracking event document model — append-only.

Every status change on an order creates a new document here; existing
events are NEVER edited or deleted. This is what makes the tracking
history immutable, per the assignment's core requirement.
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class TrackingEventInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    order_id: str
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: Optional[str] = None    # None for system-generated events
    actor_role: str                    # "customer" | "agent" | "admin" | "system"
    actor_name: str                    # denormalized for display without a join
    note: Optional[str] = None
    delivery_attempt: int = 1

    model_config = {"populate_by_name": True}
