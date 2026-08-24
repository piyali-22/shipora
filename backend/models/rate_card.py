"""
Rate card document model.

A rate card defines pricing for one (order_type, scope) combination —
e.g. "B2C intra-zone" or "B2B inter-zone". Versioned: creating a new
rate card for the same (order_type, scope) doesn't edit the old one,
it deactivates it and inserts a new version. Orders store their own
snapshot of the charges at creation time, so historical order prices
never move just because an admin tweaks a rate later.
"""
from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class OrderType(StrEnum):
    B2B = "B2B"
    B2C = "B2C"


class RateScope(StrEnum):
    INTRA_ZONE = "INTRA_ZONE"
    INTER_ZONE = "INTER_ZONE"


class RateCardInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    order_type: OrderType
    scope: RateScope

    base_charge: float          # charge for the included weight
    included_kg: float = 1.0    # weight covered by base_charge
    per_extra_kg_charge: float  # charge per kg beyond included_kg

    cod_flat_charge: float = 0.0        # flat COD surcharge
    cod_percent_of_subtotal: float = 0.0  # % COD surcharge, applied on top of flat

    version: int = 1
    is_active: bool = True
    effective_from: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
