"""
GET    /api/zones                — list all zones (any authenticated user)
GET    /api/zones/resolve/{pin}  — resolve a PIN to its zone (any authenticated user)
POST   /api/zones                — create a zone (admin)
PATCH  /api/zones/{id}           — edit name/description/active (admin)
POST   /api/zones/{id}/pincodes  — add PIN codes to a zone (admin)
DELETE /api/zones/{id}/pincodes  — remove PIN codes from a zone (admin)
DELETE /api/zones/{id}           — deactivate a zone (admin) — never hard-deletes,
                                    since historical orders may reference it
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from core.database import get_db
from core.deps import get_current_user, require_role
from models.user import UserRole
from schemas.auth import UserPublic
from schemas.zone import (
    ZoneCreateRequest,
    ZonePincodeUpdateRequest,
    ZonePublic,
    ZoneUpdateRequest,
)
from services.zone_service import resolve_zone_for_pincode

router = APIRouter()


def _to_zone_public(doc: dict) -> ZonePublic:
    return ZonePublic(
        id=str(doc["_id"]),
        name=doc["name"],
        code=doc["code"],
        description=doc.get("description"),
        pincodes=doc.get("pincodes", []),
        is_active=doc.get("is_active", True),
        pincode_count=len(doc.get("pincodes", [])),
    )


def _oid(zone_id: str) -> ObjectId:
    try:
        return ObjectId(zone_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid zone id.")


@router.get("", response_model=list[ZonePublic])
async def list_zones(current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    zones = await db.zones.find().sort("name", 1).to_list(length=500)
    return [_to_zone_public(z) for z in zones]


@router.get("/resolve/{pincode}", response_model=ZonePublic)
async def resolve_pincode(pincode: str, current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    zone_doc = await resolve_zone_for_pincode(db, pincode)
    return _to_zone_public(zone_doc)


@router.post("", response_model=ZonePublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(UserRole.ADMIN))])
async def create_zone(payload: ZoneCreateRequest):
    db = get_db()

    # Reject PINs already claimed by another active zone — a PIN
    # belonging to two zones at once would make resolution ambiguous.
    if payload.pincodes:
        clash = await db.zones.find_one({"pincodes": {"$in": payload.pincodes}, "is_active": True})
        if clash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"One or more PIN codes are already assigned to zone '{clash['name']}'.",
            )

    doc = payload.model_dump()
    try:
        result = await db.zones.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A zone with this code already exists.")

    doc["_id"] = result.inserted_id
    return _to_zone_public(doc)


@router.patch("/{zone_id}", response_model=ZonePublic,
              dependencies=[Depends(require_role(UserRole.ADMIN))])
async def update_zone(zone_id: str, payload: ZoneUpdateRequest):
    db = get_db()
    oid = _oid(zone_id)

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update.")

    result = await db.zones.find_one_and_update(
        {"_id": oid}, {"$set": updates}, return_document=True
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found.")
    return _to_zone_public(result)


@router.post("/{zone_id}/pincodes", response_model=ZonePublic,
             dependencies=[Depends(require_role(UserRole.ADMIN))])
async def add_pincodes(zone_id: str, payload: ZonePincodeUpdateRequest):
    db = get_db()
    oid = _oid(zone_id)

    clash = await db.zones.find_one(
        {"_id": {"$ne": oid}, "pincodes": {"$in": payload.pincodes}, "is_active": True}
    )
    if clash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"One or more PIN codes are already assigned to zone '{clash['name']}'.",
        )

    result = await db.zones.find_one_and_update(
        {"_id": oid},
        {"$addToSet": {"pincodes": {"$each": payload.pincodes}}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found.")
    return _to_zone_public(result)


@router.delete("/{zone_id}/pincodes", response_model=ZonePublic,
               dependencies=[Depends(require_role(UserRole.ADMIN))])
async def remove_pincodes(zone_id: str, payload: ZonePincodeUpdateRequest):
    db = get_db()
    oid = _oid(zone_id)

    result = await db.zones.find_one_and_update(
        {"_id": oid},
        {"$pullAll": {"pincodes": payload.pincodes}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found.")
    return _to_zone_public(result)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role(UserRole.ADMIN))])
async def deactivate_zone(zone_id: str):
    """Soft-delete only — orders may reference this zone historically."""
    db = get_db()
    oid = _oid(zone_id)
    result = await db.zones.update_one({"_id": oid}, {"$set": {"is_active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found.")
