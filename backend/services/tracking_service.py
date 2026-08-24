"""
Tracking service.

This is the ONLY place in the codebase allowed to (a) append a
tracking event and (b) update an order's current_status. Nothing
else touches tracking_events directly or does db.orders.update_one
on current_status — that keeps the append-only guarantee real
instead of just a convention someone can accidentally break later.
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status as http_status
from motor.motor_asyncio import AsyncIOMotorDatabase

# Valid forward transitions, per the assignment spec exactly.
# Assignment (CREATED/RESCHEDULED -> ASSIGNED) is handled by
# assignment_service, not here, so it's intentionally excluded.
VALID_TRANSITIONS: dict[str, set[str]] = {
    "ASSIGNED": {"PICKED_UP"},
    "PICKED_UP": {"IN_TRANSIT"},
    "IN_TRANSIT": {"OUT_FOR_DELIVERY"},
    "OUT_FOR_DELIVERY": {"DELIVERED", "FAILED"},
    "FAILED": {"RESCHEDULED"},
}


def validate_transition(current_status: str, new_status: str) -> None:
    """Raises 409 if this status change isn't a valid next step."""
    allowed = VALID_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Cannot move an order from '{current_status}' to '{new_status}'. "
                   f"Valid next status(es) from '{current_status}': {sorted(allowed) or 'none'}.",
        )


async def append_tracking_event(
    db: AsyncIOMotorDatabase,
    *,
    order_id: str,
    status: str,
    actor_id: str | None,
    actor_role: str,
    actor_name: str,
    note: str | None = None,
    delivery_attempt: int = 1,
) -> dict:
    """
    Appends a new tracking event and updates the order's current_status
    to match. The event itself is never edited afterward — only new
    events are ever inserted, so the full history stays intact even
    when current_status moves on.
    """
    event_doc = {
        "order_id": order_id,
        "status": status,
        "timestamp": datetime.now(timezone.utc),
        "actor_id": actor_id,
        "actor_role": actor_role,
        "actor_name": actor_name,
        "note": note,
        "delivery_attempt": delivery_attempt,
    }
    result = await db.tracking_events.insert_one(event_doc)
    event_doc["_id"] = result.inserted_id

    await db.orders.update_one(
        {"_id": _to_object_id(order_id)},
        {"$set": {"current_status": status, "updated_at": datetime.now(timezone.utc)}},
    )

    # Notify the customer on every status change, per the assignment spec.
    # A notification failure should never break the status update itself,
    # so this is deliberately best-effort and never raises upward.
    updated_order = await db.orders.find_one({"_id": _to_object_id(order_id)})
    if updated_order:
        try:
            from services.notification_service import notify_status_change
            await notify_status_change(db, order_doc=updated_order, status=status, note=note)
        except Exception as exc:  # noqa: BLE001
            import logging
            logging.getLogger("shipora.tracking").error(
                "Notification failed for order %s status %s: %s", order_id, status, exc
            )

    return event_doc


async def get_tracking_history(db: AsyncIOMotorDatabase, order_id: str) -> list[dict]:
    """Full chronological history for an order — oldest first."""
    cursor = db.tracking_events.find({"order_id": order_id}).sort("timestamp", 1)
    return await cursor.to_list(length=1000)


def _to_object_id(order_id: str):
    from bson import ObjectId
    return ObjectId(order_id)
