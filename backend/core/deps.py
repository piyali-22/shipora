"""
Auth dependencies: who is making this request, and are they allowed to.

get_current_user: decodes the bearer token, loads the user from Mongo,
    rejects if token invalid/expired or user deactivated.
require_role(...): wraps get_current_user with a role allow-list —
    used as a route dependency, e.g. Depends(require_role(UserRole.ADMIN)).
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.database import get_db
from core.security import decode_access_token, JWTError
from models.user import UserRole
from schemas.auth import UserPublic

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserPublic:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token.")

    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token.")

    db = get_db()
    user_doc = await db.users.find_one({"_id": oid})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists.")
    if not user_doc.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated.")

    return UserPublic(
        id=str(user_doc["_id"]),
        full_name=user_doc["full_name"],
        email=user_doc["email"],
        phone=user_doc.get("phone"),
        role=user_doc["role"],
        is_active=user_doc.get("is_active", True),
    )


def require_role(*allowed_roles: UserRole):
    """Route dependency factory — restricts an endpoint to specific roles."""

    async def _checker(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(r.value for r in allowed_roles)}.",
            )
        return current_user

    return _checker
