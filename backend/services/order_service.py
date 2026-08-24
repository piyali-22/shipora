"""
Order service — order creation orchestration.

Ties together: pricing engine (Phase 4) -> zone resolution (Phase 3)
-> tracking ID generation -> order persistence -> first tracking
event (Phase 5's own addition). Routes call into this rather than
assembling an order document themselves.
"""
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from models.order import OrderStatus
from models.rate_card import OrderType
from services.pricing_engine import calculate_price, extract_pincode
from services.tracking_service import append_tracking_event
from utils.tracking_id import generate_tracking_id

MAX_TRACKING_ID_ATTEMPTS = 5


async def _generate_unique_tracking_id(db: AsyncIOMotorDatabase) -> str:
    for _ in range(MAX_TRACKING_ID_ATTEMPTS):
        candidate = generate_tracking_id()
        existing = await db.orders.find_one({"tracking_id": candidate})
        if not existing:
            return candidate
    # Astronomically unlikely with a 31^7 keyspace, but fail loudly rather
    # than silently return a colliding ID if it ever somehow happens.
    raise RuntimeError("Could not generate a unique tracking ID after several attempts.")


async def create_order(
    db: AsyncIOMotorDatabase,
    *,
    customer_id: str,
    created_by_admin_id: str | None,
    pickup_address: str,
    drop_address: str,
    length_cm: float,
    breadth_cm: float,
    height_cm: float,
    actual_weight_kg: float,
    order_type: OrderType,
    payment_type: str,
    actor_role: str,
    actor_name: str,
) -> dict:
    """
    Calculates price (re-validating everything server-side — the
    frontend's earlier /quote call is never trusted as-is), persists
    the order with that price snapshotted, and writes the first
    ORDER_CREATED tracking event. Returns the full order document.
    """
    breakdown = await calculate_price(
        db,
        pickup_address=pickup_address,
        drop_address=drop_address,
        length_cm=length_cm,
        breadth_cm=breadth_cm,
        height_cm=height_cm,
        actual_weight_kg=actual_weight_kg,
        order_type=order_type,
        payment_type=payment_type,
    )
    priced = breakdown.to_dict()  # use the same rounded values the /quote preview showed

    tracking_id = await _generate_unique_tracking_id(db)

    order_doc = {
        "tracking_id": tracking_id,
        "customer_id": customer_id,
        "created_by_admin_id": created_by_admin_id,
        "pickup_address": pickup_address,
        "pickup_pincode": extract_pincode(pickup_address),
        "pickup_zone_id": breakdown.pickup_zone_id,
        "pickup_zone_name": breakdown.pickup_zone_name,
        "drop_address": drop_address,
        "drop_pincode": extract_pincode(drop_address),
        "drop_zone_id": breakdown.drop_zone_id,
        "drop_zone_name": breakdown.drop_zone_name,
        "length_cm": length_cm,
        "breadth_cm": breadth_cm,
        "height_cm": height_cm,
        "actual_weight": priced["actual_weight"],
        "volumetric_weight": priced["volumetric_weight"],
        "chargeable_weight": priced["chargeable_weight"],
        "order_type": priced["order_type"],
        "payment_type": priced["payment_type"],
        "zone_type": priced["zone_type"],
        "rate_card_id": priced["rate_card_id"],
        "rate_card_version": priced["rate_card_version"],
        "base_charge": priced["base_charge"],
        "weight_charge": priced["extra_weight_charge"],
        "cod_surcharge": priced["cod_surcharge"],
        "total_charge": priced["total"],
        "assigned_agent_id": None,
        "current_status": OrderStatus.CREATED.value,
        "delivery_attempt": 1,
        "estimated_delivery_date": None,
        "rescheduled_date": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    result = await db.orders.insert_one(order_doc)
    order_doc["_id"] = result.inserted_id

    await append_tracking_event(
        db,
        order_id=str(result.inserted_id),
        status=OrderStatus.CREATED.value,
        actor_id=customer_id if not created_by_admin_id else created_by_admin_id,
        actor_role=actor_role,
        actor_name=actor_name,
        note="Order placed" if not created_by_admin_id else "Order created by admin on customer's behalf",
    )

    return order_doc
