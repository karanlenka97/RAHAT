"""Pydantic schemas for Authentication and Authorization."""
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Schema for user credentials authentication request."""

    identifier: str = Field(
        ...,
        description="Phone number or email address of the user",
        examples=["+919000000001", "admin@rahat.local"],
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Plaintext password to authenticate",
    )


class UserSummary(BaseModel):
    """Safe user profile response schema (never contains password hash)."""

    id: uuid.UUID
    full_name: str
    phone: str
    email: Optional[str] = None
    role: Optional[str] = None
    facility_id: Optional[uuid.UUID] = None
    is_active: bool
    is_verified: bool
    permissions: List[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """OAuth2 / JWT Token response schema."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    user: UserSummary


class RefreshTokenRequest(BaseModel):
    """Schema for requesting a new access token via refresh token."""

    refresh_token: str = Field(..., description="Valid JWT refresh token")


class LogoutResponse(BaseModel):
    """Schema for logout confirmation."""

    message: str = "Successfully logged out"
