from pydantic import BaseModel, Field, field_validator

from models.rate_card import OrderType


class PriceQuoteRequest(BaseModel):
    pickup_address: str = Field(min_length=10, max_length=300)
    drop_address: str = Field(min_length=10, max_length=300)
    length_cm: float = Field(gt=0, le=1000)
    breadth_cm: float = Field(gt=0, le=1000)
    height_cm: float = Field(gt=0, le=1000)
    actual_weight_kg: float = Field(gt=0, le=1000)
    order_type: OrderType
    payment_type: str

    @field_validator("payment_type")
    @classmethod
    def validate_payment_type(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in ("PREPAID", "COD"):
            raise ValueError("payment_type must be 'PREPAID' or 'COD'")
        return v
