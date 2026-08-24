"""
GET  /api/rates                       — list rate cards (any authenticated user)
GET  /api/rates/active/{order_type}/{scope} — get the currently active card for a combo
POST /api/rates                       — create a new rate card version (admin)
PATCH /api/rates/{id}                 — edit name/active flag only, never pricing (admin)

Versioning rule: only one rate card can be active per (order_type, scope)
at a time. Creating a new active card for a combo that already has one
auto-deactivates the old one — it is never edited in place, so orders
that already stored their charge snapshot are unaffected.
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from core.deps import require_role, get_current_user
from models.rate_card import OrderType, RateScope
from models.user import UserRole
from schemas.auth import UserPublic
from schemas.rate_card import RateCardCreateRequest, RateCardPublic, RateCardUpdateRequest

router = APIRouter()


def _to_rate_public(doc: dict) -> RateCardPublic:
    return RateCardPublic(
        id=str(doc["_id"]),
        name=doc["name"],
        order_type=doc["order_type"],
        scope=doc["scope"],
        base_charge=doc["base_charge"],
        included_kg=doc["included_kg"],
        per_extra_kg_charge=doc["per_extra_kg_charge"],
        cod_flat_charge=doc.get("cod_flat_charge", 0.0),
        cod_percent_of_subtotal=doc.get("cod_percent_of_subtotal", 0.0),
        version=doc.get("version", 1),
        is_active=doc.get("is_active", True),
    )


def _oid(rate_id: str) -> ObjectId:
    try:
        return ObjectId(rate_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rate card id.")


@router.get("", response_model=list[RateCardPublic])
async def list_rate_cards(current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    cards = await db.rate_cards.find().sort([("order_type", 1), ("scope", 1), ("version", -1)]).to_list(length=500)
    return [_to_rate_public(c) for c in cards]


@router.get("/active/{order_type}/{scope}", response_model=RateCardPublic)
async def get_active_rate_card(
    order_type: OrderType, scope: RateScope, current_user: UserPublic = Depends(get_current_user)
):
    db = get_db()
    doc = await db.rate_cards.find_one(
        {"order_type": order_type.value, "scope": scope.value, "is_active": True}
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active rate card configured for {order_type.value} / {scope.value}. "
                   f"An admin needs to create one before orders of this type can be priced.",
        )
    return _to_rate_public(doc)


@router.post("", response_model=RateCardPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(UserRole.ADMIN))])
async def create_rate_card(payload: RateCardCreateRequest):
    db = get_db()

    # Find the current active card (if any) for this combo, to compute
    # the next version number and deactivate it atomically-ish.
    existing_active = await db.rate_cards.find_one(
        {"order_type": payload.order_type.value, "scope": payload.scope.value, "is_active": True}
    )
    next_version = (existing_active["version"] + 1) if existing_active else 1

    doc = payload.model_dump()
    doc["order_type"] = payload.order_type.value
    doc["scope"] = payload.scope.value
    doc["version"] = next_version

    result = await db.rate_cards.insert_one(doc)
    doc["_id"] = result.inserted_id

    if payload.is_active and existing_active:
        # New version supersedes the old one. Historical orders already
        # have their charges snapshotted onto the order document itself,
        # so deactivating this doesn't touch past pricing.
        await db.rate_cards.update_one({"_id": existing_active["_id"]}, {"$set": {"is_active": False}})

    return _to_rate_public(doc)


@router.patch("/{rate_id}", response_model=RateCardPublic,
              dependencies=[Depends(require_role(UserRole.ADMIN))])
async def update_rate_card(rate_id: str, payload: RateCardUpdateRequest):
    db = get_db()
    oid = _oid(rate_id)

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update.")

    result = await db.rate_cards.find_one_and_update(
        {"_id": oid}, {"$set": updates}, return_document=True
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate card not found.")
    return _to_rate_public(result)
