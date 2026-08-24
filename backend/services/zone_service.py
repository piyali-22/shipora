"""
Zone resolution service.

Given a PIN code, find which active zone it belongs to. This is the
ONLY place in the codebase allowed to answer "what zone is this
address in" — pricing and order creation call into this rather than
ever inspecting address strings themselves.

If a PIN isn't mapped to any zone, that's a hard validation error,
never a silent guess.
"""
import re

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

PINCODE_RE = re.compile(r"\b(\d{6})\b")


def extract_pincode(address: str) -> str:
    """
    Pulls a 6-digit PIN code out of a free-text address string.
    Raises a clear validation error if none is found — we never guess.
    """
    match = PINCODE_RE.search(address)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not find a 6-digit PIN code in the address. "
                   "Please include the PIN code (e.g. '...New Delhi 110001').",
        )
    return match.group(1)


async def resolve_zone_for_pincode(db: AsyncIOMotorDatabase, pincode: str) -> dict:
    """
    Returns the active zone document containing this PIN code.
    Raises 422 if the PIN isn't mapped to any active zone — this is
    a deliberate hard failure, not a fallback/default zone, per the
    spec: 'show a clear validation error instead of silently guessing.'
    """
    zone_doc = await db.zones.find_one({"pincodes": pincode, "is_active": True})
    if not zone_doc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"PIN code {pincode} is not mapped to any active delivery zone. "
                   f"An admin needs to add this PIN to a zone before orders can be created for it.",
        )
    return zone_doc


async def resolve_zone_for_address(db: AsyncIOMotorDatabase, address: str) -> dict:
    """Convenience wrapper: extract PIN from address text, then resolve it to a zone."""
    pincode = extract_pincode(address)
    return await resolve_zone_for_pincode(db, pincode)
