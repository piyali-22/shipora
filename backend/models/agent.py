"""
Agent profile document model.

An agent is a user (role=AGENT) plus operational data that doesn't
belong on the user record itself: which zone they operate in,
whether they're currently available, and how many active deliveries
they're carrying. One agent profile per agent user, linked by user_id.
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class AgentInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str  # references users._id where role == "agent"

    current_zone_id: str
    is_available: bool = True
    is_active: bool = True

    active_assignment_count: int = 0   # orders currently assigned, not yet delivered/failed
    total_deliveries_completed: int = 0
    total_deliveries_failed: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
