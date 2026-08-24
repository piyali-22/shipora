from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class AgentCreateRequest(BaseModel):
    """Admin creates an agent profile for an existing agent-role user."""
    agent_email: EmailStr
    zone_id: str


class AgentAvailabilityUpdateRequest(BaseModel):
    is_available: bool


class AgentZoneUpdateRequest(BaseModel):
    zone_id: str


class AgentPublic(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    current_zone_id: str
    current_zone_name: str
    is_available: bool
    is_active: bool
    active_assignment_count: int
    total_deliveries_completed: int
    total_deliveries_failed: int


class ManualAssignRequest(BaseModel):
    agent_id: str
