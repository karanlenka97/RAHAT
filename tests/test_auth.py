"""Automated tests for Authentication and RBAC."""
import uuid
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db
from app.models import Base, Role, User
from app.core.security import get_password_hash, create_access_token
from app.db.seed import seed_roles, seed_dev_users, DEV_PASSWORD_PLAIN, SYSTEM_ROLES


@pytest.fixture
def test_db_session():
    """Create an isolated in-memory SQLite database session for auth tests with StaticPool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create required tables for auth
    Role.__table__.create(engine)
    User.__table__.create(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed roles and dev users
    seed_roles(session)
    seed_dev_users(session)

    yield session

    session.close()


@pytest.fixture
def auth_client(test_db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_login_success_with_email(auth_client):
    """1. Verify valid login with email returns access token and user profile."""
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@rahat.local"
    assert data["user"]["role"] == "ADMIN"
    # Ensure password hash is NEVER returned
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]


def test_login_success_with_phone(auth_client):
    """1b. Verify valid login with phone returns access token and user profile."""
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"identifier": "+919000000008", "password": DEV_PASSWORD_PLAIN},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["phone"] == "+919000000008"
    assert data["user"]["role"] == "ASHA"


def test_login_invalid_password_fails(auth_client):
    """2. Verify login with wrong password returns 401 Unauthorized."""
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@rahat.local", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert "Invalid phone/email or password" in response.json()["detail"]


def test_login_unknown_user_fails(auth_client):
    """3. Verify login with unknown user returns 401 Unauthorized."""
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"identifier": "nonexistent@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    assert response.status_code == 401
    assert "Invalid phone/email or password" in response.json()["detail"]


def test_login_inactive_user_rejected(auth_client, test_db_session):
    """4. Verify inactive user is rejected with 403 Forbidden."""
    # Deactivate user
    user = test_db_session.query(User).filter(User.email == "doctor@rahat.local").first()
    user.is_active = False
    test_db_session.commit()

    response = auth_client.post(
        "/api/v1/auth/login",
        json={"identifier": "doctor@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


def test_password_stored_as_hash_not_plaintext(test_db_session):
    """5. Verify password in database is stored as a bcrypt hash."""
    user = test_db_session.query(User).filter(User.email == "admin@rahat.local").first()
    assert user.hashed_password != DEV_PASSWORD_PLAIN
    assert user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2a$")


def test_get_me_valid_jwt(auth_client):
    """7, 11, 12. Verify valid JWT is accepted by /auth/me and returns identity and role."""
    login_res = auth_client.post(
        "/api/v1/auth/login",
        json={"identifier": "doctor@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    token = login_res.json()["access_token"]

    response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "doctor@rahat.local"
    assert user_data["role"] == "DOCTOR"
    assert "patient:read" in user_data["permissions"]


def test_invalid_jwt_rejected(auth_client):
    """8. Verify invalid/malformed JWT is rejected with 401."""
    response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.string"},
    )
    assert response.status_code == 401


def test_expired_jwt_rejected(auth_client, test_db_session):
    """9. Verify expired JWT is rejected with 401."""
    user = test_db_session.query(User).filter(User.email == "admin@rahat.local").first()
    # Create token that expired 10 minutes ago
    expired_token = create_access_token(
        subject=user.id,
        role="ADMIN",
        expires_delta=timedelta(minutes=-10),
    )

    response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_missing_jwt_rejected(auth_client):
    """10. Verify missing Authorization header returns 401."""
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_rbac_authorization(auth_client):
    """13, 14. Verify role authorization (require_roles): allows authorized, blocks unauthorized."""
    # Login as ASHA
    asha_login = auth_client.post(
        "/api/v1/auth/login",
        json={"identifier": "asha@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    asha_token = asha_login.json()["access_token"]

    # Login as Doctor
    doc_login = auth_client.post(
        "/api/v1/auth/login",
        json={"identifier": "doctor@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    doc_token = doc_login.json()["access_token"]

    # Login as Admin
    admin_login = auth_client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    admin_token = admin_login.json()["access_token"]

    # Test clinical endpoint (/test-clinical requires DOCTOR or MEDICAL_OFFICER)
    # ASHA should get 403 Forbidden
    res_asha = auth_client.get(
        "/api/v1/auth/test-clinical",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert res_asha.status_code == 403

    # DOCTOR should get 200 OK
    res_doc = auth_client.get(
        "/api/v1/auth/test-clinical",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res_doc.status_code == 200
    assert "Clinical authorization granted" in res_doc.json()["message"]

    # ADMIN has global bypass access and should get 200 OK
    res_admin = auth_client.get(
        "/api/v1/auth/test-clinical",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200


def test_refresh_token_flow(auth_client):
    """15. Verify refreshing an access token using a valid refresh token."""
    login_res = auth_client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    refresh_token = login_res.json()["refresh_token"]

    refresh_res = auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@rahat.local"


def test_logout_endpoint(auth_client):
    """16. Verify logout returns successful message."""
    response = auth_client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert "logged out" in response.json()["message"].lower()
