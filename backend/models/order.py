"""
Order document model.

The price breakdown fields (base_charge, weight_charge, cod_surcharge,
total_charge, chargeable_weight, etc.) are a SNAPSHOT taken at order
creation time — never recomputed later. This is what makes rule #16
from the spec true: "Historical order prices must remain stable even
if rate cards change later."
"""
from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class OrderStatus(StrEnum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RESCHEDULED = "RESCHEDULED"


class OrderInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    tracking_id: str
    customer_id: str
    created_by_admin_id: Optional[str] = None  # set if an admin created this on the customer's behalf

    pickup_address: str
    pickup_pincode: str
    pickup_zone_id: str
    pickup_zone_name: str

    drop_address: str
    drop_pincode: str
    drop_zone_id: str
    drop_zone_name: str

    length_cm: float
    breadth_cm: float
    height_cm: float
    actual_weight: float
    volumetric_weight: float
    chargeable_weight: float

    order_type: str   # "B2B" | "B2C"
    payment_type: str  # "PREPAID" | "COD"
    zone_type: str     # "INTRA_ZONE" | "INTER_ZONE"

    # Snapshotted pricing — never recalculated after creation
    rate_card_id: str
    rate_card_version: int
    base_charge: float
    weight_charge: float
    cod_surcharge: float
    total_charge: float

    assigned_agent_id: Optional[str] = None
    current_status: OrderStatus = OrderStatus.CREATED
    delivery_attempt: int = 1
    estimated_delivery_date: Optional[datetime] = None
    rescheduled_date: Optional[datetime] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
