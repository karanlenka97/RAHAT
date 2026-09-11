"""Authentication and Authorization API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserSummary,
    RefreshTokenRequest,
    LogoutResponse,
)
from app.services.auth_service import (
    authenticate_user,
    build_user_summary,
    generate_auth_tokens,
    refresh_access_token,
)

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="Authenticate with phone number or email and password to obtain JWT access & refresh tokens.",
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate credentials and generate token pair."""
    user = authenticate_user(db, login_data.identifier, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Please contact your system administrator.",
        )

    return generate_auth_tokens(user)


@router.get(
    "/me",
    response_model=UserSummary,
    summary="Current User Profile",
    description="Retrieve the profile, role, and permissions of the currently authenticated user.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserSummary:
    """Return the profile of the authenticated user."""
    return build_user_summary(current_user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Access Token",
    description="Exchange a valid JWT refresh token for a newly issued access token.",
)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Validate refresh token and issue new token pair."""
    try:
        return refresh_access_token(db, refresh_data.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User Logout",
    description="Log out the current user and clear client session state.",
)
def logout() -> LogoutResponse:
    """Clear client authentication session."""
    return LogoutResponse(message="Successfully logged out.")


# Sample role-protected verification routes
@router.get(
    "/test-admin",
    response_model=dict,
    summary="RBAC Test (Admin only)",
    description="Verification endpoint accessible only by ADMIN role.",
)
def test_admin_access(
    current_user: User = require_roles("ADMIN"),
) -> dict:
    """Protected endpoint for ADMIN role."""
    return {"message": "Admin authorization granted", "user": current_user.full_name}


@router.get(
    "/test-clinical",
    response_model=dict,
    summary="RBAC Test (Clinical roles)",
    description="Verification endpoint accessible by DOCTOR, MEDICAL_OFFICER, and ADMIN.",
)
def test_clinical_access(
    current_user: User = require_roles("DOCTOR", "MEDICAL_OFFICER"),
) -> dict:
    """Protected endpoint for clinical roles."""
    return {"message": "Clinical authorization granted", "user": current_user.full_name}
