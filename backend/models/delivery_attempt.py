"""
Delivery attempt document model.

A failed delivery doesn't destroy anything — it closes out one attempt
and, on reschedule, a new attempt begins. All attempts for an order
stay in the database side by side, so "attempt 1 failed, attempt 2
delivered" is a real queryable history, not just inferred from the
main tracking_events log.
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class DeliveryAttemptInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    order_id: str
    attempt_number: int
    agent_id: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "ASSIGNED"  # ASSIGNED | DELIVERED | FAILED
    failure_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
