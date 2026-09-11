"""Tests for database foundation, models, metadata, relationships, Alembic, and PostGIS configuration."""
import os
import uuid
import importlib.util
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import (
    Base,
    Role,
    User,
    Village,
    Facility,
    FacilityCapability,
    HealthcareProfessional,
    Patient,
    CareRequest,
    Referral,
    ReferralEvent,
    FollowUp,
    Notification,
    AuditLog,
)
from app.db.seed import seed_roles, SYSTEM_ROLES


EXPECTED_TABLES = {
    "roles",
    "facilities",
    "villages",
    "facility_capabilities",
    "users",
    "healthcare_professionals",
    "patients",
    "care_requests",
    "referrals",
    "referral_events",
    "follow_ups",
    "notifications",
    "audit_logs",
}


def test_all_13_models_registered_in_metadata():
    """Verify that all 13 required domain models are registered in Base.metadata."""
    registered_tables = set(Base.metadata.tables.keys())
    for table_name in EXPECTED_TABLES:
        assert table_name in registered_tables, f"Missing table in metadata: {table_name}"


def test_postgis_geometry_columns():
    """Verify that Village and Facility contain PostGIS spatial Geometry columns with SRID 4326."""
    village_table = Base.metadata.tables["villages"]
    facility_table = Base.metadata.tables["facilities"]

    assert "location" in village_table.columns
    assert "location" in facility_table.columns

    # Verify SRID 4326 for WGS 84 GPS coordinates
    assert village_table.columns["location"].type.srid == 4326
    assert facility_table.columns["location"].type.srid == 4326
    assert village_table.columns["location"].type.geometry_type == "POINT"
    assert facility_table.columns["location"].type.geometry_type == "POINT"


def test_model_foreign_key_definitions():
    """Verify key foreign key references across models."""
    tables = Base.metadata.tables

    # User -> Role, Facility
    user_fks = {fk.target_fullname for fk in tables["users"].foreign_keys}
    assert "roles.id" in user_fks
    assert "facilities.id" in user_fks

    # Village -> Facility
    village_fks = {fk.target_fullname for fk in tables["villages"].foreign_keys}
    assert "facilities.id" in village_fks

    # FacilityCapability -> Facility
    cap_fks = {fk.target_fullname for fk in tables["facility_capabilities"].foreign_keys}
    assert "facilities.id" in cap_fks

    # HealthcareProfessional -> User, Facility
    hp_fks = {fk.target_fullname for fk in tables["healthcare_professionals"].foreign_keys}
    assert "users.id" in hp_fks
    assert "facilities.id" in hp_fks

    # CareRequest -> Patient, Village, Facility, User, HealthcareProfessional
    cr_fks = {fk.target_fullname for fk in tables["care_requests"].foreign_keys}
    assert "patients.id" in cr_fks
    assert "villages.id" in cr_fks
    assert "facilities.id" in cr_fks
    assert "users.id" in cr_fks
    assert "healthcare_professionals.id" in cr_fks

    # Referral -> CareRequest, Patient, Facilities, User
    ref_fks = {fk.target_fullname for fk in tables["referrals"].foreign_keys}
    assert "care_requests.id" in ref_fks
    assert "patients.id" in ref_fks
    assert "facilities.id" in ref_fks
    assert "users.id" in ref_fks

    # ReferralEvent -> Referral, User
    re_fks = {fk.target_fullname for fk in tables["referral_events"].foreign_keys}
    assert "referrals.id" in re_fks
    assert "users.id" in re_fks

    # FollowUp -> Referral, Patient, User
    fu_fks = {fk.target_fullname for fk in tables["follow_ups"].foreign_keys}
    assert "referrals.id" in fu_fks
    assert "patients.id" in fu_fks
    assert "users.id" in fu_fks

    # Notification & AuditLog -> User
    assert "users.id" in {fk.target_fullname for fk in tables["notifications"].foreign_keys}
    assert "users.id" in {fk.target_fullname for fk in tables["audit_logs"].foreign_keys}


def test_unique_constraints_and_indexes():
    """Verify unique constraints and database indexes."""
    tables = Base.metadata.tables

    # Unique columns
    assert tables["roles"].columns["name"].unique is True
    assert tables["users"].columns["phone"].unique is True
    assert tables["users"].columns["email"].unique is True
    assert tables["patients"].columns["anonymous_patient_code"].unique is True
    assert tables["care_requests"].columns["request_number"].unique is True
    assert tables["referrals"].columns["referral_code"].unique is True
    assert tables["referrals"].columns["care_request_id"].index is True


def test_alembic_migration_file():
    """Verify Alembic initial migration exists, is importable, and defines upgrade/downgrade."""
    migration_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "backend",
            "alembic",
            "versions",
            "0001_initial_database_foundation.py",
        )
    )
    assert os.path.exists(migration_path), "Migration 0001 file does not exist"

    spec = importlib.util.spec_from_file_location("migration_0001", migration_path)
    migration_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_mod)

    assert hasattr(migration_mod, "upgrade")
    assert hasattr(migration_mod, "downgrade")
    assert migration_mod.revision == "0001_initial_database_foundation"
    assert migration_mod.down_revision is None


@pytest.fixture
def sqlite_session():
    """Create an in-memory SQLite session for testing non-spatial model logic and seeding."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Role.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_role_seeding_and_uniqueness(sqlite_session):
    """Verify idempotent role seeding and unique constraints for exact specification roles."""
    created_first = seed_roles(sqlite_session)
    assert created_first == len(SYSTEM_ROLES)

    # Re-running seed should not duplicate roles
    created_second = seed_roles(sqlite_session)
    assert created_second == 0

    roles = sqlite_session.query(Role).all()
    assert len(roles) == len(SYSTEM_ROLES)
    role_names = {r.name for r in roles}
    assert "ADMIN" in role_names
    assert "DOCTOR" in role_names
    assert "ASHA" in role_names
    assert "CHO" in role_names
    assert "ANM" in role_names


def test_model_instantiation():
    """Verify that model instances can be created with expected default fields."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        phone="+919876543210",
        full_name="Dr. Ananya Sharma",
        hashed_password="argon2_hashed_placeholder",
        is_active=True,
    )
    assert user.id == user_id
    assert user.phone == "+919876543210"
    assert user.is_active is True
    assert "hashed_password" in user.__dict__

    patient_id = uuid.uuid4()
    patient = Patient(
        id=patient_id,
        anonymous_patient_code="RAHAT-PT-001001",
        full_name="Ramesh Kumar",
        age=45,
        gender="MALE",
    )
    assert patient.anonymous_patient_code == "RAHAT-PT-001001"
    assert patient.gender == "MALE"

    facility_id = uuid.uuid4()
    facility = Facility(
        id=facility_id,
        name="District Hospital Sundargarh",
        facility_type="DH",
        district="Sundargarh",
        state="Odisha",
        latitude=22.12,
        longitude=84.03,
        total_beds=150,
        available_beds=42,
    )
    assert facility.name == "District Hospital Sundargarh"
    assert facility.available_beds == 42
