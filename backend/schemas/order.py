from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from models.rate_card import OrderType
from schemas.pricing import PriceQuoteRequest


class OrderCreateRequest(PriceQuoteRequest):
    """Same shape as a quote request — creating an order is 'confirm this quote.'"""
    pass


class AdminOrderCreateRequest(OrderCreateRequest):
    """Admin creating an order on behalf of a customer — needs to specify who the customer is."""
    customer_email: EmailStr


class OrderStatusUpdateRequest(BaseModel):
    """Agent moves an order to the next status in its lifecycle."""
    status: str
    note: Optional[str] = Field(default=None, max_length=500)
    failure_reason: Optional[str] = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def uppercase_status(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("failure_reason")
    @classmethod
    def require_reason_when_failed(cls, v, info):
        # Cross-field check enforced again in the route/service layer too,
        # since Pydantic validator ordering across fields isn't guaranteed.
        return v


class RescheduleRequest(BaseModel):
    """Customer (or admin) reschedules a FAILED delivery for a new date."""
    rescheduled_date: datetime


class AdminOverrideStatusRequest(BaseModel):
    """Admin force-sets an order's status, bypassing normal transition rules.
    Still creates a tracking event clearly attributed to the admin override."""
    status: str
    note: str = Field(min_length=3, max_length=500)

    @field_validator("status")
    @classmethod
    def uppercase_status(cls, v: str) -> str:
        return v.strip().upper()


class TrackingEventPublic(BaseModel):
    status: str
    timestamp: datetime
    actor_role: str
    actor_name: str
    note: Optional[str] = None
    delivery_attempt: int


class OrderPublic(BaseModel):
    id: str
    tracking_id: str
    customer_id: str

    pickup_address: str
    pickup_zone_name: str
    drop_address: str
    drop_zone_name: str

    length_cm: float
    breadth_cm: float
    height_cm: float
    actual_weight: float
    volumetric_weight: float
    chargeable_weight: float

    order_type: OrderType
    payment_type: str
    zone_type: str

    base_charge: float
    weight_charge: float
    cod_surcharge: float
    total_charge: float

    assigned_agent_id: Optional[str] = None
    current_status: str
    delivery_attempt: int

    created_at: datetime


class OrderWithTrackingPublic(OrderPublic):
    tracking_history: list[TrackingEventPublic]
