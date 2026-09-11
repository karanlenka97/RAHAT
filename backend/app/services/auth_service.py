"""Authentication business logic service."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas.auth import UserSummary, TokenResponse


def get_user_by_identifier(db: Session, identifier: str) -> Optional[User]:
    """Find a user by either email or phone number."""
    cleaned = identifier.strip()
    return db.query(User).filter(
        or_(
            User.email == cleaned.lower(),
            User.phone == cleaned,
        )
    ).first()


def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
    """Authenticate user credentials against stored bcrypt hash."""
    user = get_user_by_identifier(db, identifier)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def build_user_summary(user: User) -> UserSummary:
    """Build a clean UserSummary schema from a User model."""
    role_name = user.role.name if user.role else None
    permissions = user.role.permissions if user.role and user.role.permissions else []
    if isinstance(permissions, list):
        role_permissions = [str(p) for p in permissions]
    else:
        role_permissions = []

    return UserSummary(
        id=user.id,
        full_name=user.full_name,
        phone=user.phone,
        email=user.email,
        role=role_name,
        facility_id=user.facility_id,
        is_active=user.is_active,
        is_verified=user.is_verified,
        permissions=role_permissions,
    )


def generate_auth_tokens(user: User) -> TokenResponse:
    """Generate access and refresh tokens for an authenticated user."""
    role_name = user.role.name if user.role else "USER"
    access_token = create_access_token(subject=user.id, role=role_name)
    refresh_token = create_refresh_token(subject=user.id, role=role_name)
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=build_user_summary(user),
    )


def refresh_access_token(db: Session, refresh_token_str: str) -> TokenResponse:
    """Validate refresh token and issue a new token pair."""
    payload = decode_token(refresh_token_str)
    if payload.get("type") != "refresh":
        raise ValueError("Invalid token type. Expected refresh token.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise ValueError("Token missing user subject.")

    user = db.query(User).filter(User.id == uuid.UUID(user_id_str)).first()
    if not user or not user.is_active:
        raise ValueError("User not found or inactive.")

    return generate_auth_tokens(user)
