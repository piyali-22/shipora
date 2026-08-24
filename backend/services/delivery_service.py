"""
Delivery service — status updates, failure handling, and reschedule.

Everything here goes through tracking_service.append_tracking_event()
for the actual status change + history write, and additionally
maintains the per-attempt record in delivery_attempts so "attempt 1
failed, attempt 2 delivered" is real queryable data, not just
inferred from timestamps in the main tracking log.
"""
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status as http_status
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.tracking_service import append_tracking_event, validate_transition


def _oid(value: str, label: str) -> ObjectId:
    try:
        return ObjectId(value)
    except InvalidId:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Invalid {label} id.")


async def _get_order_or_404(db: AsyncIOMotorDatabase, order_id: str) -> dict:
    doc = await db.orders.find_one({"_id": _oid(order_id, "order")})
    if not doc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return doc


async def update_status_as_agent(
    db: AsyncIOMotorDatabase,
    *,
    order_id: str,
    agent_user_id: str,
    new_status: str,
    note: str | None,
    failure_reason: str | None,
    actor_name: str,
) -> dict:
    """
    Agent moves an order forward one step. Only the agent this order is
    assigned to may do this — an agent updating an order that isn't
    theirs is a 403, not just an oversight the frontend happens to hide.
    """
    order_doc = await _get_order_or_404(db, order_id)

    agent_profile = await db.agents.find_one({"user_id": agent_user_id})
    if not agent_profile or order_doc.get("assigned_agent_id") != str(agent_profile["_id"]):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="This order is not assigned to you — you can only update your own deliveries.",
        )

    current_status = order_doc["current_status"]
    validate_transition(current_status, new_status)

    if new_status == "FAILED" and not failure_reason:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A failure_reason is required when marking a delivery as FAILED.",
        )

    attempt_number = order_doc.get("delivery_attempt", 1)
    now = datetime.now(timezone.utc)

    # Keep the per-attempt record in sync
    attempt_update: dict = {}
    if new_status == "PICKED_UP":
        attempt_update = {"started_at": now, "status": "IN_PROGRESS"}
    elif new_status == "DELIVERED":
        attempt_update = {"completed_at": now, "status": "DELIVERED"}
    elif new_status == "FAILED":
        attempt_update = {"completed_at": now, "status": "FAILED", "failure_reason": failure_reason}

    if attempt_update:
        await db.delivery_attempts.update_one(
            {"order_id": order_id, "attempt_number": attempt_number},
            {"$set": attempt_update},
        )

    # Update agent load/stats on terminal outcomes
    if new_status == "DELIVERED":
        await db.agents.update_one(
            {"_id": agent_profile["_id"]},
            {"$inc": {"active_assignment_count": -1, "total_deliveries_completed": 1}},
        )
    elif new_status == "FAILED":
        await db.agents.update_one(
            {"_id": agent_profile["_id"]},
            {"$inc": {"active_assignment_count": -1, "total_deliveries_failed": 1}},
        )

    await append_tracking_event(
        db,
        order_id=order_id,
        status=new_status,
        actor_id=agent_user_id,
        actor_role="agent",
        actor_name=actor_name,
        note=note or (f"Failure reason: {failure_reason}" if new_status == "FAILED" else None),
        delivery_attempt=attempt_number,
    )

    return await db.orders.find_one({"_id": order_doc["_id"]})


async def reschedule_delivery(
    db: AsyncIOMotorDatabase,
    *,
    order_id: str,
    rescheduled_date: datetime,
    actor_id: str,
    actor_role: str,
    actor_name: str,
) -> dict:
    """
    Customer (or admin) reschedules a FAILED delivery. Starts a new
    delivery attempt, frees the order for reassignment, and — critically
    — never touches the tracking events from the failed attempt. Those
    stay exactly as they were; only new events get appended from here.
    """
    order_doc = await _get_order_or_404(db, order_id)

    if order_doc["current_status"] != "FAILED":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Only a FAILED delivery can be rescheduled. This order is currently '{order_doc['current_status']}'.",
        )

    new_attempt_number = order_doc.get("delivery_attempt", 1) + 1

    await db.orders.update_one(
        {"_id": order_doc["_id"]},
        {"$set": {
            "rescheduled_date": rescheduled_date,
            "delivery_attempt": new_attempt_number,
            "assigned_agent_id": None,  # cleared — a fresh assign/auto-assign call is required
        }},
    )

    await db.delivery_attempts.insert_one({
        "order_id": order_id,
        "attempt_number": new_attempt_number,
        "agent_id": None,
        "scheduled_date": rescheduled_date,
        "started_at": None,
        "completed_at": None,
        "status": "SCHEDULED",
        "failure_reason": None,
        "notes": None,
        "created_at": datetime.now(timezone.utc),
    })

    await append_tracking_event(
        db,
        order_id=order_id,
        status="RESCHEDULED",
        actor_id=actor_id,
        actor_role=actor_role,
        actor_name=actor_name,
        note=f"Delivery rescheduled for {rescheduled_date.isoformat()}. Awaiting agent reassignment.",
        delivery_attempt=new_attempt_number,
    )

    return await db.orders.find_one({"_id": order_doc["_id"]})


async def override_status_as_admin(
    db: AsyncIOMotorDatabase,
    *,
    order_id: str,
    new_status: str,
    note: str,
    actor_id: str,
    actor_name: str,
) -> dict:
    """
    Admin force-sets status, bypassing the normal transition rules —
    but the resulting tracking event is unambiguously marked as an
    admin override, so the audit trail never looks like an organic
    agent-driven transition.
    """
    order_doc = await _get_order_or_404(db, order_id)

    await append_tracking_event(
        db,
        order_id=order_id,
        status=new_status,
        actor_id=actor_id,
        actor_role="admin",
        actor_name=actor_name,
        note=f"[ADMIN OVERRIDE] {note}",
        delivery_attempt=order_doc.get("delivery_attempt", 1),
    )

    return await db.orders.find_one({"_id": order_doc["_id"]})
