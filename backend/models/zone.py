"""
Zone document model.

A zone is a named region (e.g. "Delhi NCR", "Mumbai Metro") made up
of one or more 6-digit PIN codes. Pricing and routing both key off
zone, not raw address text — this is the thing that stops pricing
logic from turning into a pile of `if "Mumbai" in address` hacks.
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class ZoneInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    code: str  # short unique code, e.g. "ZN-NCR" — used in UI/route labels
    description: Optional[str] = None
    pincodes: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
