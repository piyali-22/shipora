"""
Pricing engine — the core rate calculation logic for Shipora.

This module is the single source of truth for "what should this
shipment cost." Nothing upstream (routes, frontend) is allowed to
compute or guess a price — they call into calculate_price() and
trust its answer completely. This is what makes the backend, not
the frontend, the source of truth for pricing.

Calculation order (mirrors the assignment spec exactly):
  1. Resolve pickup zone and drop zone from PIN codes
  2. Determine INTRA_ZONE vs INTER_ZONE
  3. Compute volumetric weight = (L x B x H) / 5000
  4. Chargeable weight = max(actual_weight, volumetric_weight)
  5. Look up the active rate card for (order_type, zone_type)
  6. base_charge + (extra kg beyond included_kg) x per_extra_kg_charge
  7. If COD: add flat COD surcharge + percentage-of-subtotal surcharge
  8. Return a complete, itemized breakdown — nothing is hidden or assumed
"""
from dataclasses import dataclass

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.rate_card import OrderType, RateScope
from services.zone_service import resolve_zone_for_pincode, extract_pincode

VOLUMETRIC_DIVISOR = 5000  # standard L(cm) x B(cm) x H(cm) / 5000 convention


@dataclass
class PriceBreakdown:
    actual_weight: float
    volumetric_weight: float
    chargeable_weight: float

    pickup_zone_id: str
    pickup_zone_name: str
    pickup_zone_code: str
    drop_zone_id: str
    drop_zone_name: str
    drop_zone_code: str
    zone_type: str  # "INTRA_ZONE" | "INTER_ZONE"

    order_type: str
    payment_type: str

    rate_card_id: str
    rate_card_version: int

    base_charge: float
    extra_weight_charge: float
    subtotal: float
    cod_surcharge: float
    total: float

    def to_dict(self) -> dict:
        return {
            "actual_weight": round(self.actual_weight, 3),
            "volumetric_weight": round(self.volumetric_weight, 3),
            "chargeable_weight": round(self.chargeable_weight, 3),
            "pickup_zone": {
                "id": self.pickup_zone_id, "name": self.pickup_zone_name, "code": self.pickup_zone_code,
            },
            "drop_zone": {
                "id": self.drop_zone_id, "name": self.drop_zone_name, "code": self.drop_zone_code,
            },
            "zone_type": self.zone_type,
            "order_type": self.order_type,
            "payment_type": self.payment_type,
            "rate_card_id": self.rate_card_id,
            "rate_card_version": self.rate_card_version,
            "base_charge": round(self.base_charge, 2),
            "extra_weight_charge": round(self.extra_weight_charge, 2),
            "subtotal": round(self.subtotal, 2),
            "cod_surcharge": round(self.cod_surcharge, 2),
            "total": round(self.total, 2),
        }


def calculate_volumetric_weight(length_cm: float, breadth_cm: float, height_cm: float) -> float:
    return (length_cm * breadth_cm * height_cm) / VOLUMETRIC_DIVISOR


def calculate_chargeable_weight(actual_weight_kg: float, volumetric_weight_kg: float) -> float:
    return max(actual_weight_kg, volumetric_weight_kg)


async def _get_active_rate_card(db: AsyncIOMotorDatabase, order_type: str, scope: str) -> dict:
    doc = await db.rate_cards.find_one({"order_type": order_type, "scope": scope, "is_active": True})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No active rate card configured for {order_type} / {scope}. "
                   f"An admin needs to create one before this shipment can be priced.",
        )
    return doc


async def calculate_price(
    db: AsyncIOMotorDatabase,
    *,
    pickup_address: str,
    drop_address: str,
    length_cm: float,
    breadth_cm: float,
    height_cm: float,
    actual_weight_kg: float,
    order_type: OrderType,
    payment_type: str,  # "PREPAID" | "COD"
) -> PriceBreakdown:
    """
    The one function everything else calls. Raises HTTPException with a
    clear detail message on any validation failure (unmapped PIN, no
    active rate card) rather than ever falling back to a guessed price.
    """
    # 1. Resolve zones from addresses (extract_pincode raises 422 if no PIN found)
    pickup_pincode = extract_pincode(pickup_address)
    drop_pincode = extract_pincode(drop_address)

    pickup_zone = await resolve_zone_for_pincode(db, pickup_pincode)
    drop_zone = await resolve_zone_for_pincode(db, drop_pincode)

    # 2. Zone type
    zone_type = RateScope.INTRA_ZONE if pickup_zone["_id"] == drop_zone["_id"] else RateScope.INTER_ZONE

    # 3 & 4. Weight
    volumetric_weight = calculate_volumetric_weight(length_cm, breadth_cm, height_cm)
    chargeable_weight = calculate_chargeable_weight(actual_weight_kg, volumetric_weight)

    # 5. Rate card lookup
    rate_card = await _get_active_rate_card(db, order_type.value, zone_type.value)

    # 6. Base + extra weight charge
    base_charge = rate_card["base_charge"]
    included_kg = rate_card["included_kg"]
    extra_kg = max(0.0, chargeable_weight - included_kg)
    extra_weight_charge = extra_kg * rate_card["per_extra_kg_charge"]
    subtotal = base_charge + extra_weight_charge

    # 7. COD surcharge
    cod_surcharge = 0.0
    if payment_type.upper() == "COD":
        flat = rate_card.get("cod_flat_charge", 0.0)
        pct = rate_card.get("cod_percent_of_subtotal", 0.0)
        cod_surcharge = flat + (subtotal * pct / 100.0)

    total = subtotal + cod_surcharge

    return PriceBreakdown(
        actual_weight=actual_weight_kg,
        volumetric_weight=volumetric_weight,
        chargeable_weight=chargeable_weight,
        pickup_zone_id=str(pickup_zone["_id"]),
        pickup_zone_name=pickup_zone["name"],
        pickup_zone_code=pickup_zone["code"],
        drop_zone_id=str(drop_zone["_id"]),
        drop_zone_name=drop_zone["name"],
        drop_zone_code=drop_zone["code"],
        zone_type=zone_type.value,
        order_type=order_type.value,
        payment_type=payment_type.upper(),
        rate_card_id=str(rate_card["_id"]),
        rate_card_version=rate_card.get("version", 1),
        base_charge=base_charge,
        extra_weight_charge=extra_weight_charge,
        subtotal=subtotal,
        cod_surcharge=cod_surcharge,
        total=total,
    )
