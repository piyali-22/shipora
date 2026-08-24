"""
POST /api/auth/register       — public customer self-registration
POST /api/auth/login          — any role
GET  /api/auth/me             — current user's own profile
POST /api/auth/admin/create   — admin provisions agent/admin/customer accounts
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from core.database import get_db
from core.deps import get_current_user, require_role
from core.security import create_access_token, hash_password, verify_password
from models.user import UserRole
from schemas.auth import (
    AdminCreateUserRequest,
    CustomerRegisterRequest,
    LoginRequest,
    TokenResponse,
    UserPublic,
)

router = APIRouter()


def _to_user_public(doc: dict) -> UserPublic:
    return UserPublic(
        id=str(doc["_id"]),
        full_name=doc["full_name"],
        email=doc["email"],
        phone=doc.get("phone"),
        role=doc["role"],
        is_active=doc.get("is_active", True),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_customer(payload: CustomerRegisterRequest):
    db = get_db()

    doc = {
        "full_name": payload.full_name.strip(),
        "email": payload.email.lower(),
        "phone": payload.phone,
        "hashed_password": hash_password(payload.password),
        "role": UserRole.CUSTOMER.value,
        "is_active": True,
    }

    try:
        result = await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    doc["_id"] = result.inserted_id
    token = create_access_token(subject=str(result.inserted_id), role=UserRole.CUSTOMER.value)
    return TokenResponse(access_token=token, user=_to_user_public(doc))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    db = get_db()
    doc = await db.users.find_one({"email": payload.email.lower()})

    # Deliberately identical error for "no such user" and "wrong password"
    # — don't leak which emails are registered.
    if not doc or not verify_password(payload.password, doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact support.",
        )

    token = create_access_token(subject=str(doc["_id"]), role=doc["role"])
    return TokenResponse(access_token=token, user=_to_user_public(doc))


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: UserPublic = Depends(get_current_user)):
    return current_user


@router.post(
    "/admin/create",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def admin_create_user(payload: AdminCreateUserRequest):
    """
    Lets an admin provision agent or admin accounts (and customer
    accounts on a customer's behalf), since there's no public
    self-registration path for agents/admins.
    """
    db = get_db()

    doc = {
        "full_name": payload.full_name.strip(),
        "email": payload.email.lower(),
        "phone": payload.phone,
        "hashed_password": hash_password(payload.password),
        "role": payload.role.value,
        "is_active": True,
    }

    try:
        result = await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    doc["_id"] = result.inserted_id
    return _to_user_public(doc)
