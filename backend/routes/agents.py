"""
POST  /api/agents                    — admin creates an agent profile for an existing agent-role user
GET   /api/agents                    — admin lists all agents
GET   /api/agents/me                 — agent views their own profile
PATCH /api/agents/me/availability    — agent toggles their own availability
PATCH /api/agents/{agent_id}/zone    — admin reassigns an agent's operating zone
GET   /api/agents/me/deliveries      — agent lists orders currently assigned to them
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from core.deps import get_current_user, require_role
from models.user import UserRole
from schemas.agent import AgentAvailabilityUpdateRequest, AgentCreateRequest, AgentPublic, AgentZoneUpdateRequest
from schemas.auth import UserPublic
from schemas.order import OrderPublic

router = APIRouter()


async def _to_agent_public(db, doc: dict) -> AgentPublic:
    user_doc = await db.users.find_one({"_id": ObjectId(doc["user_id"])})
    zone_doc = await db.zones.find_one({"_id": ObjectId(doc["current_zone_id"])})
    return AgentPublic(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        full_name=user_doc["full_name"] if user_doc else "Unknown",
        email=user_doc["email"] if user_doc else "unknown@shipora.app",
        phone=user_doc.get("phone") if user_doc else None,
        current_zone_id=doc["current_zone_id"],
        current_zone_name=zone_doc["name"] if zone_doc else "Unknown Zone",
        is_available=doc.get("is_available", True),
        is_active=doc.get("is_active", True),
        active_assignment_count=doc.get("active_assignment_count", 0),
        total_deliveries_completed=doc.get("total_deliveries_completed", 0),
        total_deliveries_failed=doc.get("total_deliveries_failed", 0),
    )


@router.post("", response_model=AgentPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(UserRole.ADMIN))])
async def create_agent_profile(payload: AgentCreateRequest):
    db = get_db()

    agent_user = await db.users.find_one({"email": payload.agent_email.lower(), "role": UserRole.AGENT.value})
    if not agent_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No agent-role account found with email {payload.agent_email}. "
                   f"Create the account first via /api/auth/admin/create with role='agent'.",
        )

    existing_profile = await db.agents.find_one({"user_id": str(agent_user["_id"])})
    if existing_profile:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This agent already has a profile.")

    zone_doc = await db.zones.find_one({"_id": ObjectId(payload.zone_id), "is_active": True})
    if not zone_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found or inactive.")

    doc = {
        "user_id": str(agent_user["_id"]),
        "current_zone_id": payload.zone_id,
        "is_available": True,
        "is_active": True,
        "active_assignment_count": 0,
        "total_deliveries_completed": 0,
        "total_deliveries_failed": 0,
    }
    result = await db.agents.insert_one(doc)
    doc["_id"] = result.inserted_id
    return await _to_agent_public(db, doc)


@router.get("", response_model=list[AgentPublic], dependencies=[Depends(require_role(UserRole.ADMIN))])
async def list_agents():
    db = get_db()
    docs = await db.agents.find().to_list(length=500)
    return [await _to_agent_public(db, d) for d in docs]


@router.get("/me", response_model=AgentPublic, dependencies=[Depends(require_role(UserRole.AGENT))])
async def get_my_agent_profile(current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    doc = await db.agents.find_one({"user_id": current_user.id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No agent profile set up for this account yet. An admin needs to create one.",
        )
    return await _to_agent_public(db, doc)


@router.patch("/me/availability", response_model=AgentPublic, dependencies=[Depends(require_role(UserRole.AGENT))])
async def update_my_availability(payload: AgentAvailabilityUpdateRequest, current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    result = await db.agents.find_one_and_update(
        {"user_id": current_user.id},
        {"$set": {"is_available": payload.is_available}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No agent profile found for this account.")
    return await _to_agent_public(db, result)


@router.patch("/{agent_id}/zone", response_model=AgentPublic, dependencies=[Depends(require_role(UserRole.ADMIN))])
async def update_agent_zone(agent_id: str, payload: AgentZoneUpdateRequest):
    db = get_db()
    try:
        agent_oid = ObjectId(agent_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent id.")

    zone_doc = await db.zones.find_one({"_id": ObjectId(payload.zone_id), "is_active": True})
    if not zone_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found or inactive.")

    result = await db.agents.find_one_and_update(
        {"_id": agent_oid}, {"$set": {"current_zone_id": payload.zone_id}}, return_document=True
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
    return await _to_agent_public(db, result)


@router.get("/me/deliveries", response_model=list[OrderPublic], dependencies=[Depends(require_role(UserRole.AGENT))])
async def list_my_deliveries(current_user: UserPublic = Depends(get_current_user)):
    """Orders currently assigned to the logged-in agent."""
    from routes.orders import _to_order_public  # local import avoids a circular import at module load time

    db = get_db()
    agent_doc = await db.agents.find_one({"user_id": current_user.id})
    if not agent_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No agent profile found for this account.")

    docs = await db.orders.find({"assigned_agent_id": str(agent_doc["_id"])}).sort("created_at", -1).to_list(length=200)
    return [_to_order_public(d) for d in docs]
