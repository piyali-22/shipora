"""
Assignment service — manual and automatic agent assignment.

Both paths converge on _assign(): persisted to MongoDB, never just a
UI-level change, and always appends an ASSIGNED tracking event through
tracking_service so the append-only history guarantee holds here too.

Auto-assignment algorithm (spec: "nearest suitable available agent"):
  1. Filter to agents who are active + available
  2. Filter to agents in the order's pickup zone (our proxy for
     "nearest" — we don't have live GPS coordinates, so same-zone is
     the meaningful notion of proximity this system actually has)
  3. Among those, pick the one with the fewest active assignments
     (load-balancing tiebreaker) — ties broken by whoever has been
     idle longest (oldest updated_at)
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.order import OrderStatus
from services.tracking_service import append_tracking_event

# An order can only be (re)assigned while in one of these states.
ASSIGNABLE_STATUSES = {OrderStatus.CREATED.value, OrderStatus.ASSIGNED.value, OrderStatus.RESCHEDULED.value}


def _oid(value: str, label: str) -> ObjectId:
    try:
        return ObjectId(value)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {label} id.")


async def _get_assignable_order(db: AsyncIOMotorDatabase, order_id: str) -> dict:
    order_doc = await db.orders.find_one({"_id": _oid(order_id, "order")})
    if not order_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if order_doc["current_status"] not in ASSIGNABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order is currently '{order_doc['current_status']}' and cannot be assigned or reassigned.",
        )
    return order_doc


async def _assign(
    db: AsyncIOMotorDatabase,
    *,
    order_doc: dict,
    agent_doc: dict,
    actor_id: str,
    actor_role: str,
    actor_name: str,
    note: str,
) -> dict:
    order_id = str(order_doc["_id"])
    previous_agent_id = order_doc.get("assigned_agent_id")

    # If this order was already assigned to a different agent, free up
    # that agent's load count before taking on the new one.
    if previous_agent_id and previous_agent_id != str(agent_doc["_id"]):
        await db.agents.update_one(
            {"_id": ObjectId(previous_agent_id)},
            {"$inc": {"active_assignment_count": -1}},
        )

    await db.orders.update_one(
        {"_id": order_doc["_id"]},
        {"$set": {"assigned_agent_id": str(agent_doc["_id"])}},
    )
    if not previous_agent_id or previous_agent_id != str(agent_doc["_id"]):
        await db.agents.update_one(
            {"_id": agent_doc["_id"]},
            {"$inc": {"active_assignment_count": 1}},
        )

    await append_tracking_event(
        db,
        order_id=order_id,
        status=OrderStatus.ASSIGNED.value,
        actor_id=actor_id,
        actor_role=actor_role,
        actor_name=actor_name,
        note=note,
        delivery_attempt=order_doc.get("delivery_attempt", 1),
    )

    updated_order = await db.orders.find_one({"_id": order_doc["_id"]})
    return updated_order


async def manual_assign(
    db: AsyncIOMotorDatabase, *, order_id: str, agent_id: str, actor_id: str, actor_name: str
) -> dict:
    order_doc = await _get_assignable_order(db, order_id)

    agent_doc = await db.agents.find_one({"_id": _oid(agent_id, "agent")})
    if not agent_doc or not agent_doc.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found or inactive.")

    agent_user = await db.users.find_one({"_id": ObjectId(agent_doc["user_id"])})
    agent_name = agent_user["full_name"] if agent_user else "Unknown Agent"

    return await _assign(
        db, order_doc=order_doc, agent_doc=agent_doc,
        actor_id=actor_id, actor_role="admin", actor_name=actor_name,
        note=f"Manually assigned to {agent_name} by admin.",
    )


async def auto_assign(db: AsyncIOMotorDatabase, *, order_id: str, actor_id: str, actor_name: str) -> dict:
    order_doc = await _get_assignable_order(db, order_id)
    pickup_zone_id = order_doc["pickup_zone_id"]

    candidates = await db.agents.find({
        "is_active": True,
        "is_available": True,
        "current_zone_id": pickup_zone_id,
    }).sort([("active_assignment_count", 1), ("updated_at", 1)]).to_list(length=50)

    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No available delivery agents in the selected zone.",
        )

    chosen_agent = candidates[0]
    agent_user = await db.users.find_one({"_id": ObjectId(chosen_agent["user_id"])})
    agent_name = agent_user["full_name"] if agent_user else "Unknown Agent"

    return await _assign(
        db, order_doc=order_doc, agent_doc=chosen_agent,
        actor_id=actor_id, actor_role="admin", actor_name=actor_name,
        note=f"Auto-assigned to nearest available agent: {agent_name}.",
    )
