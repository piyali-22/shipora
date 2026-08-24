"""
Request/response schemas for auth endpoints.

Kept separate from models/user.py: models describe what's stored in
Mongo, schemas describe what crosses the API boundary. A schema never
includes hashed_password in a response.
"""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from models.user import UserRole


class CustomerRegisterRequest(BaseModel):
    """Public self-registration — always creates a CUSTOMER, never agent/admin."""
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class AdminCreateUserRequest(BaseModel):
    """
    Admin-only: create an agent or admin account (or a customer on a
    customer's behalf, per assignment rule "Admin can create orders on
    behalf of a customer" — account creation follows the same pattern).
    """
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v: UserRole) -> UserRole:
        # all three roles are technically allowed here — admins can
        # provision other admins, agents, or customer accounts
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """Safe-to-return user shape — never includes hashed_password."""
    id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
