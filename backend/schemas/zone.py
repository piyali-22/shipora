from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _validate_pincode(v: str) -> str:
    v = v.strip()
    if not (v.isdigit() and len(v) == 6):
        raise ValueError(f"'{v}' is not a valid 6-digit PIN code.")
    return v


class ZoneCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    code: str = Field(min_length=2, max_length=20)
    description: Optional[str] = None
    pincodes: list[str] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("pincodes")
    @classmethod
    def validate_pincodes(cls, v: list[str]) -> list[str]:
        return [_validate_pincode(p) for p in v]

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.strip().upper()


class ZoneUpdateRequest(BaseModel):
    """All fields optional — only provided fields are patched."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ZonePincodeUpdateRequest(BaseModel):
    pincodes: list[str]

    @field_validator("pincodes")
    @classmethod
    def validate_pincodes(cls, v: list[str]) -> list[str]:
        return [_validate_pincode(p) for p in v]


class ZonePublic(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str] = None
    pincodes: list[str]
    is_active: bool
    pincode_count: int
