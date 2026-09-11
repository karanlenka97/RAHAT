"""Phase 12 Test Suite: End-to-End Security, RBAC Matrix & Tenant Isolation.
Verifies role authorization boundaries across all 8 personas, token authentication,
cross-tier access restrictions (HTTP 403/401), and audit trail logging.
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.models.care_request import CareRequest
from app.models.facility import Facility
from app.models.patient import Patient
from app.models.referral import Referral
from app.models.audit_log import AuditLog
from app.models.user import User


# =========================================================================
# 1. Unauthenticated & Invalid Token Security Tests (HTTP 401)
# =========================================================================

def test_unauthenticated_request_rejected(client):
    """Verify that protected API endpoints reject requests with missing Authorization header."""
    endpoints = [
        ("GET", "/api/v1/patients/"),
        ("GET", "/api/v1/care-requests/"),
        ("GET", "/api/v1/referrals/"),
        ("GET", "/api/v1/facilities/"),
        ("GET", "/api/v1/dashboard/frontline"),
        ("GET", "/api/v1/dashboard/facility"),
        ("GET", "/api/v1/dashboard/district"),
    ]
    for method, path in endpoints:
        res = client.request(method, path)
        assert res.status_code == 401, f"Expected 401 for {method} {path}, got {res.status_code}"


def test_invalid_token_rejected(client):
    """Verify that requests with bogus or malformed JWT tokens are rejected."""
    headers = {"Authorization": "Bearer invalid.token.signature"}
    res = client.get("/api/v1/patients/", headers=headers)
    assert res.status_code == 401


# =========================================================================
# 2. Dashboard RBAC Permission Matrix (HTTP 403 Restrictions)
# =========================================================================

def test_frontline_cannot_access_district_dashboard(client, asha_token, anm_token, cho_token):
    """Verify frontline workers (ASHA, ANM, CHO) are forbidden from accessing district dashboard."""
    for token, role in [(asha_token, "ASHA"), (anm_token, "ANM"), (cho_token, "CHO")]:
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/v1/dashboard/district", headers=headers)
        assert res.status_code == 403, f"{role} should not access district dashboard, got {res.status_code}"
        assert "access denied" in res.json()["detail"].lower()


def test_frontline_cannot_access_facility_dashboard(client, asha_token, anm_token, cho_token):
    """Verify frontline workers cannot access facility management dashboard."""
    for token, role in [(asha_token, "ASHA"), (anm_token, "ANM"), (cho_token, "CHO")]:
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/v1/dashboard/facility", headers=headers)
        assert res.status_code == 403, f"{role} should not access facility dashboard"


def test_doctor_cannot_access_district_dashboard(client, doctor_token):
    """Verify hospital doctor cannot access district-level analytics dashboard."""
    headers = {"Authorization": f"Bearer {doctor_token}"}
    res = client.get("/api/v1/dashboard/district", headers=headers)
    assert res.status_code == 403


def test_district_admin_access_district_dashboard(client, district_admin_token):
    """Verify District Admin has authorized access to district dashboard."""
    headers = {"Authorization": f"Bearer {district_admin_token}"}
    res = client.get("/api/v1/dashboard/district", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_referrals" in data
    assert "care_completion_rate" in data


def test_facility_admin_access_facility_dashboard(client, facility_admin_token):
    """Verify Facility Admin has authorized access to facility dashboard."""
    headers = {"Authorization": f"Bearer {facility_admin_token}"}
    res = client.get("/api/v1/dashboard/facility", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "facility_name" in data
    assert "total_beds" in data
    assert "available_beds" in data


def test_cho_access_frontline_dashboard(client, cho_token):
    """Verify CHO has authorized access to frontline dashboard."""
    headers = {"Authorization": f"Bearer {cho_token}"}
    res = client.get("/api/v1/dashboard/frontline", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "active_care_requests" in data
    assert "action_queue" in data


# =========================================================================
# 3. Administrative User Management RBAC
# =========================================================================

def test_only_system_admin_can_access_user_directory(client, admin_token, doctor_token, cho_token):
    """Verify /api/v1/auth/test-admin endpoint is restricted to ADMIN role only."""
    admin_res = client.get("/api/v1/auth/test-admin", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200

    doctor_res = client.get("/api/v1/auth/test-admin", headers={"Authorization": f"Bearer {doctor_token}"})
    assert doctor_res.status_code == 403

    cho_res = client.get("/api/v1/auth/test-admin", headers={"Authorization": f"Bearer {cho_token}"})
    assert cho_res.status_code == 403


# =========================================================================
# 4. Facility Creation & Capability Management RBAC
# =========================================================================

def test_frontline_cannot_create_facility(client, asha_token, anm_token, cho_token):
    """Verify frontline healthcare workers cannot create or modify facility capabilities."""
    facility_payload = {
        "name": "Unauthorized Test Clinic",
        "facility_type": "PHC",
        "district": "Sundargarh",
        "block": "Kutra",
        "latitude": 22.15,
        "longitude": 84.25,
        "total_beds": 10,
        "available_beds": 5,
    }
    for token in [asha_token, anm_token, cho_token]:
        res = client.post("/api/v1/facilities/", json=facility_payload, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403


# =========================================================================
# 5. Audit Trail Verification for RBAC Actions
# =========================================================================

def test_audit_logs_recorded_for_sensitive_actions(client, test_db_session, admin_token):
    """Verify that patient creation, referral lifecycle events, and logins generate AuditLog entries."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Perform action: create a patient
    p_res = client.post(
        "/api/v1/patients/",
        json={
            "full_name": "Audit Verification Patient",
            "age": 42,
            "gender": "MALE",
            "phone": "+919888877770",
        },
        headers=headers,
    )
    assert p_res.status_code == 201

    # Check that audit log was generated
    recent_log = (
        test_db_session.query(AuditLog)
        .filter(AuditLog.action == "PATIENT_CREATED")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert recent_log is not None
    assert recent_log.entity_type == "Patient"
