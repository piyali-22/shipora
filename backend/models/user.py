"""
User document model.

One 'users' collection holds all three roles (customer/agent/admin) —
role is just a field, not a separate collection, since auth logic
(hashing, login, JWT) is identical across roles. Role-specific data
(agent's zone/availability) lives in a separate 'agents' collection
keyed by user_id, added in a later phase.
"""
from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(StrEnum):
    CUSTOMER = "customer"
    AGENT = "agent"
    ADMIN = "admin"


class UserInDB(BaseModel):
    """Shape of a document in the 'users' collection."""
    id: Optional[str] = Field(default=None, alias="_id")
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    hashed_password: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
