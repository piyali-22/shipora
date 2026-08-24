"""
POST /api/orders/quote            — price preview, nothing persisted (Phase 4)
POST /api/orders                  — customer creates + confirms an order
POST /api/orders/admin            — admin creates an order on a customer's behalf
GET  /api/orders                  — list the current user's own orders (customer),
                                     or ALL orders (admin) — role-scoped in one endpoint
GET  /api/orders/{order_id}       — single order detail + full tracking history
GET  /api/orders/track/{tracking_id} — PUBLIC tracking lookup, no auth required
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from core.deps import get_current_user, require_role
from models.user import UserRole
from schemas.auth import UserPublic
from schemas.agent import ManualAssignRequest
from schemas.order import (
    AdminOrderCreateRequest,
    AdminOverrideStatusRequest,
    OrderCreateRequest,
    OrderPublic,
    OrderStatusUpdateRequest,
    OrderWithTrackingPublic,
    RescheduleRequest,
    TrackingEventPublic,
)
from schemas.pricing import PriceQuoteRequest
from services.assignment_service import auto_assign, manual_assign
from services.delivery_service import override_status_as_admin, reschedule_delivery, update_status_as_agent
from services.order_service import create_order
from services.pricing_engine import calculate_price
from services.tracking_service import get_tracking_history

router = APIRouter()


def _to_order_public(doc: dict) -> OrderPublic:
    return OrderPublic(
        id=str(doc["_id"]),
        tracking_id=doc["tracking_id"],
        customer_id=doc["customer_id"],
        pickup_address=doc["pickup_address"],
        pickup_zone_name=doc["pickup_zone_name"],
        drop_address=doc["drop_address"],
        drop_zone_name=doc["drop_zone_name"],
        length_cm=doc["length_cm"],
        breadth_cm=doc["breadth_cm"],
        height_cm=doc["height_cm"],
        actual_weight=doc["actual_weight"],
        volumetric_weight=doc["volumetric_weight"],
        chargeable_weight=doc["chargeable_weight"],
        order_type=doc["order_type"],
        payment_type=doc["payment_type"],
        zone_type=doc["zone_type"],
        base_charge=doc["base_charge"],
        weight_charge=doc["weight_charge"],
        cod_surcharge=doc["cod_surcharge"],
        total_charge=doc["total_charge"],
        assigned_agent_id=doc.get("assigned_agent_id"),
        current_status=doc["current_status"],
        delivery_attempt=doc.get("delivery_attempt", 1),
        created_at=doc["created_at"],
    )


def _oid(order_id: str) -> ObjectId:
    try:
        return ObjectId(order_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order id.")


def _to_order_with_tracking(doc: dict, history: list[dict]) -> OrderWithTrackingPublic:
    order_public = _to_order_public(doc)
    return OrderWithTrackingPublic(
        **order_public.model_dump(),
        tracking_history=[
            TrackingEventPublic(
                status=e["status"], timestamp=e["timestamp"], actor_role=e["actor_role"],
                actor_name=e["actor_name"], note=e.get("note"), delivery_attempt=e.get("delivery_attempt", 1),
            )
            for e in history
        ],
    )


@router.post("/quote")
async def get_price_quote(payload: PriceQuoteRequest, current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    breakdown = await calculate_price(
        db,
        pickup_address=payload.pickup_address,
        drop_address=payload.drop_address,
        length_cm=payload.length_cm,
        breadth_cm=payload.breadth_cm,
        height_cm=payload.height_cm,
        actual_weight_kg=payload.actual_weight_kg,
        order_type=payload.order_type,
        payment_type=payload.payment_type,
    )
    return breakdown.to_dict()


@router.post("", response_model=OrderPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(UserRole.CUSTOMER))])
async def create_own_order(payload: OrderCreateRequest, current_user: UserPublic = Depends(get_current_user)):
    """Customer confirms a shipment for themselves."""
    db = get_db()
    doc = await create_order(
        db,
        customer_id=current_user.id,
        created_by_admin_id=None,
        pickup_address=payload.pickup_address,
        drop_address=payload.drop_address,
        length_cm=payload.length_cm,
        breadth_cm=payload.breadth_cm,
        height_cm=payload.height_cm,
        actual_weight_kg=payload.actual_weight_kg,
        order_type=payload.order_type,
        payment_type=payload.payment_type,
        actor_role="customer",
        actor_name=current_user.full_name,
    )
    return _to_order_public(doc)


@router.post("/admin", response_model=OrderPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(UserRole.ADMIN))])
async def create_order_for_customer(payload: AdminOrderCreateRequest, current_user: UserPublic = Depends(get_current_user)):
    """Admin creates an order on behalf of an existing customer, identified by email."""
    db = get_db()
    customer_doc = await db.users.find_one({"email": payload.customer_email.lower(), "role": UserRole.CUSTOMER.value})
    if not customer_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No customer account found with email {payload.customer_email}.",
        )

    doc = await create_order(
        db,
        customer_id=str(customer_doc["_id"]),
        created_by_admin_id=current_user.id,
        pickup_address=payload.pickup_address,
        drop_address=payload.drop_address,
        length_cm=payload.length_cm,
        breadth_cm=payload.breadth_cm,
        height_cm=payload.height_cm,
        actual_weight_kg=payload.actual_weight_kg,
        order_type=payload.order_type,
        payment_type=payload.payment_type,
        actor_role="admin",
        actor_name=current_user.full_name,
    )
    return _to_order_public(doc)


@router.get("", response_model=list[OrderPublic])
async def list_orders(current_user: UserPublic = Depends(get_current_user)):
    """
    Customers see only their own orders. Admins see every order.
    Agents aren't expected to use this — they get their assigned
    deliveries from a dedicated endpoint added in Phase 6.
    """
    db = get_db()
    query = {} if current_user.role == UserRole.ADMIN else {"customer_id": current_user.id}
    docs = await db.orders.find(query).sort("created_at", -1).to_list(length=500)
    return [_to_order_public(d) for d in docs]


@router.get("/track/{tracking_id}", response_model=OrderWithTrackingPublic)
async def track_order_public(tracking_id: str):
    """Public tracking lookup — no authentication required, per the assignment spec."""
    db = get_db()
    doc = await db.orders.find_one({"tracking_id": tracking_id.upper()})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No shipment found with this tracking ID.")

    history = await get_tracking_history(db, str(doc["_id"]))
    return _to_order_with_tracking(doc, history)


@router.get("/{order_id}", response_model=OrderWithTrackingPublic)
async def get_order_detail(order_id: str, current_user: UserPublic = Depends(get_current_user)):
    """Authenticated detail view — customers can only view their own orders; admins can view any."""
    db = get_db()
    oid = _oid(order_id)
    doc = await db.orders.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if current_user.role != UserRole.ADMIN and doc["customer_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this order.")

    history = await get_tracking_history(db, order_id)
    return _to_order_with_tracking(doc, history)


@router.post("/{order_id}/assign", response_model=OrderPublic,
             dependencies=[Depends(require_role(UserRole.ADMIN))])
async def assign_agent_manually(order_id: str, payload: ManualAssignRequest, current_user: UserPublic = Depends(get_current_user)):
    """Admin manually assigns a specific agent to an order."""
    db = get_db()
    updated_order = await manual_assign(
        db, order_id=order_id, agent_id=payload.agent_id,
        actor_id=current_user.id, actor_name=current_user.full_name,
    )
    return _to_order_public(updated_order)


@router.post("/{order_id}/auto-assign", response_model=OrderPublic,
             dependencies=[Depends(require_role(UserRole.ADMIN))])
async def trigger_auto_assign(order_id: str, current_user: UserPublic = Depends(get_current_user)):
    """Admin triggers automatic assignment to the nearest suitable available agent."""
    db = get_db()
    updated_order = await auto_assign(db, order_id=order_id, actor_id=current_user.id, actor_name=current_user.full_name)
    return _to_order_public(updated_order)


@router.patch("/{order_id}/status", response_model=OrderPublic,
              dependencies=[Depends(require_role(UserRole.AGENT))])
async def update_delivery_status(order_id: str, payload: OrderStatusUpdateRequest, current_user: UserPublic = Depends(get_current_user)):
    """
    Agent advances an order through its lifecycle: PICKED_UP -> IN_TRANSIT
    -> OUT_FOR_DELIVERY -> DELIVERED, or OUT_FOR_DELIVERY -> FAILED (with
    a required failure_reason). Only the agent this order is assigned to
    may call this. Invalid transitions (e.g. skipping a step) are rejected.
    """
    db = get_db()
    updated_order = await update_status_as_agent(
        db, order_id=order_id, agent_user_id=current_user.id, new_status=payload.status,
        note=payload.note, failure_reason=payload.failure_reason, actor_name=current_user.full_name,
    )
    return _to_order_public(updated_order)


@router.post("/{order_id}/reschedule", response_model=OrderPublic)
async def reschedule_order(order_id: str, payload: RescheduleRequest, current_user: UserPublic = Depends(get_current_user)):
    """
    Customer (or admin) reschedules a FAILED delivery for a new date.
    Starts a new delivery attempt and clears the previous agent
    assignment — the order needs to go through /assign or /auto-assign
    again afterward. The failed attempt's tracking history is untouched.
    """
    db = get_db()
    order_doc = await db.orders.find_one({"_id": _oid(order_id)})
    if not order_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if current_user.role != UserRole.ADMIN and order_doc["customer_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this order.")

    updated_order = await reschedule_delivery(
        db, order_id=order_id, rescheduled_date=payload.rescheduled_date,
        actor_id=current_user.id, actor_role=current_user.role.value, actor_name=current_user.full_name,
    )
    return _to_order_public(updated_order)


@router.post("/{order_id}/override-status", response_model=OrderPublic,
             dependencies=[Depends(require_role(UserRole.ADMIN))])
async def override_order_status(order_id: str, payload: AdminOverrideStatusRequest, current_user: UserPublic = Depends(get_current_user)):
    """Admin force-sets an order's status, bypassing normal transition rules — still fully audited."""
    db = get_db()
    updated_order = await override_status_as_admin(
        db, order_id=order_id, new_status=payload.status, note=payload.note,
        actor_id=current_user.id, actor_name=current_user.full_name,
    )
    return _to_order_public(updated_order)
