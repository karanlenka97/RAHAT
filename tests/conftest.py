"""Pytest test fixtures and SQLite spatial mocks."""
import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Register SQLite dummy spatial functions for in-memory unit tests
@event.listens_for(Engine, "connect")
def set_sqlite_spatial_mock(dbapi_connection, connection_record):
    if hasattr(dbapi_connection, "create_function"):
        funcs = [
            "InitSpatialMetaData",
            "RecoverGeometryColumn",
            "AddGeometryColumn",
            "DiscardGeometryColumn",
            "CreateSpatialIndex",
            "DropSpatialIndex",
            "DisableSpatialIndex",
            "CheckSpatialIndex",
            "AsEWKB",
            "AsBinary",
            "ST_AsBinary",
            "GeomFromText",
            "GeomFromEWKT",
            "ST_GeomFromEWKT",
            "ST_GeomFromText",
            "GeomFromWKB",
            "ST_AsGeoJSON",
            "ST_Transform",
            "ST_Distance",
            "ST_DWithin",
        ]
        for name in funcs:
            try:
                dbapi_connection.create_function(
                    name,
                    -1,
                    lambda *args: None if len(args) == 0 else args[0] if isinstance(args[0], (bytes, memoryview, str)) else None,
                )
            except Exception:
                pass

from app.main import app


@pytest.fixture
def client():
    """Create a FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client
