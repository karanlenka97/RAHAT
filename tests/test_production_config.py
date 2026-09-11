"""Phase 13 Test Suite: Production Configuration, Security & Health Check Readiness.
Validates production mode security constraints, JWT secret validation, CORS parsing,
and container readiness probes.
"""
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.health import HealthCheckResponse


# =========================================================================
# 1. Production Settings Security & Mode Validation
# =========================================================================

def test_development_mode_allows_dev_secret():
    """Verify development mode allows default development JWT secret and DEBUG=True."""
    s = Settings(
        ENVIRONMENT="development",
        DEBUG=True,
        JWT_SECRET="rahat-dev-insecure-secret-key-change-in-production-2026",
    )
    assert s.ENVIRONMENT == "development"
    assert s.DEBUG is True


def test_production_mode_rejects_default_insecure_jwt_secret():
    """Verify production mode strictly rejects the default development JWT secret."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            JWT_SECRET="rahat-dev-insecure-secret-key-change-in-production-2026",
        )
    assert "Production Security Error" in str(exc_info.value)


def test_production_mode_rejects_short_jwt_secret():
    """Verify production mode rejects JWT secrets shorter than 32 characters."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            JWT_SECRET="short-secret-123",
        )
    assert "Production Security Error" in str(exc_info.value)


def test_production_mode_valid_secure_secret():
    """Verify production mode succeeds with strong 64-char hex secret and sets DEBUG=False."""
    secure_secret = "a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef"
    s = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        JWT_SECRET=secure_secret,
    )
    assert s.ENVIRONMENT == "production"
    assert s.DEBUG is False
    assert s.JWT_SECRET == secure_secret


# =========================================================================
# 2. CORS Origins Parsing
# =========================================================================

def test_cors_origins_comma_separated_parsing():
    """Verify comma-separated string of origins parses into list."""
    s = Settings(
        BACKEND_CORS_ORIGINS="https://rahat.gov.in, https://health.odisha.gov.in",
    )
    assert s.BACKEND_CORS_ORIGINS == ["https://rahat.gov.in", "https://health.odisha.gov.in"]


def test_cors_origins_list_parsing():
    """Verify list of origins is preserved."""
    origins = ["https://app.rahat.local", "https://api.rahat.local"]
    s = Settings(BACKEND_CORS_ORIGINS=origins)
    assert s.BACKEND_CORS_ORIGINS == origins


# =========================================================================
# 3. Health & Readiness Endpoints
# =========================================================================

def test_liveness_health_endpoint(client):
    """Verify /health returns HTTP 200 with service and version information."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "rahat-backend"
    assert "version" in data
    assert "environment" in data


def test_readiness_probe_endpoint(client):
    """Verify /ready probe returns HTTP 200 and database connected status."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_api_v1_health_and_readiness(client):
    """Verify /api/v1/health and /api/v1/health/ready endpoints."""
    res1 = client.get("/api/v1/health")
    assert res1.status_code == 200
    assert res1.json()["status"] == "ok"

    res2 = client.get("/api/v1/health/ready")
    assert res2.status_code == 200
    assert res2.json()["database"] == "connected"
