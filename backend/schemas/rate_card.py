from typing import Optional

from pydantic import BaseModel, Field

from models.rate_card import OrderType, RateScope


class RateCardCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    order_type: OrderType
    scope: RateScope
    base_charge: float = Field(gt=0)
    included_kg: float = Field(default=1.0, gt=0)
    per_extra_kg_charge: float = Field(gt=0)
    cod_flat_charge: float = Field(default=0.0, ge=0)
    cod_percent_of_subtotal: float = Field(default=0.0, ge=0, le=100)
    is_active: bool = True


class RateCardUpdateRequest(BaseModel):
    """
    Patch-style update for non-pricing fields only (name, active flag).
    Pricing fields are intentionally NOT editable here — changing a
    price means creating a new version via /rates, never mutating an
    existing card, so historical orders stay accurate.
    """
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    is_active: Optional[bool] = None


class RateCardPublic(BaseModel):
    id: str
    name: str
    order_type: OrderType
    scope: RateScope
    base_charge: float
    included_kg: float
    per_extra_kg_charge: float
    cod_flat_charge: float
    cod_percent_of_subtotal: float
    version: int
    is_active: bool
