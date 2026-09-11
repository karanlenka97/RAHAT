"""Initial Database Foundation (13 Tables & PostGIS)

Revision ID: 0001_initial_database_foundation
Revises: 
Create Date: 2026-09-12 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = "0001_initial_database_foundation"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Enable PostGIS Extension if on PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 1. roles
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("permissions", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)
    op.create_index(op.f("ix_roles_created_at"), "roles", ["created_at"], unique=False)

    # 2. facilities
    op.create_table(
        "facilities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("facility_type", sa.String(length=50), nullable=False),
        sa.Column("tier_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("address_line", sa.String(length=255), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("pincode", sa.String(length=10), nullable=True),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=True,
            ),
            nullable=True,
        ),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("operational_status", sa.String(length=50), server_default="OPERATIONAL", nullable=False),
        sa.Column("total_beds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("available_beds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("icu_beds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("available_icu_beds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("oxygen_supported_beds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("available_oxygen_beds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ventilators_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("available_ventilators", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_facilities_name"), "facilities", ["name"], unique=False)
    op.create_index(op.f("ix_facilities_code"), "facilities", ["code"], unique=True)
    op.create_index(op.f("ix_facilities_facility_type"), "facilities", ["facility_type"], unique=False)
    op.create_index(op.f("ix_facilities_tier_level"), "facilities", ["tier_level"], unique=False)
    op.create_index(op.f("ix_facilities_district"), "facilities", ["district"], unique=False)
    op.create_index(op.f("ix_facilities_state"), "facilities", ["state"], unique=False)
    op.create_index(op.f("ix_facilities_pincode"), "facilities", ["pincode"], unique=False)
    op.create_index(op.f("ix_facilities_is_active"), "facilities", ["is_active"], unique=False)
    op.create_index(op.f("ix_facilities_created_at"), "facilities", ["created_at"], unique=False)
    op.create_index("idx_facility_type_district", "facilities", ["facility_type", "district"], unique=False)
    op.create_index("idx_facility_beds", "facilities", ["available_beds", "available_icu_beds"], unique=False)

    # 3. villages
    op.create_table(
        "villages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("sub_district_tehsil", sa.String(length=100), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("pincode", sa.String(length=10), nullable=True),
        sa.Column("population", sa.Integer(), nullable=True),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=True,
            ),
            nullable=True,
        ),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("assigned_phc_facility_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_phc_facility_id"], ["facilities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_villages_name"), "villages", ["name"], unique=False)
    op.create_index(op.f("ix_villages_code"), "villages", ["code"], unique=True)
    op.create_index(op.f("ix_villages_sub_district_tehsil"), "villages", ["sub_district_tehsil"], unique=False)
    op.create_index(op.f("ix_villages_district"), "villages", ["district"], unique=False)
    op.create_index(op.f("ix_villages_state"), "villages", ["state"], unique=False)
    op.create_index(op.f("ix_villages_pincode"), "villages", ["pincode"], unique=False)
    op.create_index(op.f("ix_villages_assigned_phc_facility_id"), "villages", ["assigned_phc_facility_id"], unique=False)
    op.create_index(op.f("ix_villages_created_at"), "villages", ["created_at"], unique=False)
    op.create_index("idx_villages_state_district", "villages", ["state", "district"], unique=False)

    # 4. facility_capabilities
    op.create_table(
        "facility_capabilities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("facility_id", sa.UUID(), nullable=False),
        sa.Column("capability_type", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("is_available_24x7", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("current_status", sa.String(length=50), server_default="AVAILABLE", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("facility_id", "capability_type", "name", name="uq_facility_capability"),
    )
    op.create_index(op.f("ix_facility_capabilities_facility_id"), "facility_capabilities", ["facility_id"], unique=False)
    op.create_index(op.f("ix_facility_capabilities_capability_type"), "facility_capabilities", ["capability_type"], unique=False)
    op.create_index(op.f("ix_facility_capabilities_name"), "facility_capabilities", ["name"], unique=False)
    op.create_index("idx_capability_lookup", "facility_capabilities", ["capability_type", "name", "current_status"], unique=False)

    # 5. users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=True),
        sa.Column("facility_id", sa.UUID(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)
    op.create_index(op.f("ix_users_full_name"), "users", ["full_name"], unique=False)
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"], unique=False)
    op.create_index(op.f("ix_users_facility_id"), "users", ["facility_id"], unique=False)
    op.create_index(op.f("ix_users_created_at"), "users", ["created_at"], unique=False)
    op.create_index("idx_users_active_role", "users", ["is_active", "role_id"], unique=False)

    # 6. healthcare_professionals
    op.create_table(
        "healthcare_professionals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("facility_id", sa.UUID(), nullable=True),
        sa.Column("professional_type", sa.String(length=50), nullable=False),
        sa.Column("registration_number", sa.String(length=100), nullable=True),
        sa.Column("specialization", sa.String(length=150), nullable=True),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("qualification", sa.String(length=150), nullable=True),
        sa.Column("duty_status", sa.String(length=50), server_default="ON_DUTY", nullable=False),
        sa.Column("contact_number", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_healthcare_professionals_professional_type"), "healthcare_professionals", ["professional_type"], unique=False)
    op.create_index(op.f("ix_healthcare_professionals_registration_number"), "healthcare_professionals", ["registration_number"], unique=True)
    op.create_index(op.f("ix_healthcare_professionals_specialization"), "healthcare_professionals", ["specialization"], unique=False)
    op.create_index(op.f("ix_healthcare_professionals_duty_status"), "healthcare_professionals", ["duty_status"], unique=False)
    op.create_index(op.f("ix_healthcare_professionals_facility_id"), "healthcare_professionals", ["facility_id"], unique=False)
    op.create_index("idx_prof_spec_facility", "healthcare_professionals", ["specialization", "facility_id"], unique=False)

    # 7. patients
    op.create_table(
        "patients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("abha_id", sa.String(length=50), nullable=True),
        sa.Column("anonymous_patient_code", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=False),
        sa.Column("blood_group", sa.String(length=10), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("emergency_contact_name", sa.String(length=150), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(length=20), nullable=True),
        sa.Column("village_id", sa.UUID(), nullable=True),
        sa.Column("address_line", sa.String(length=255), nullable=True),
        sa.Column("chronic_conditions", sa.JSON(), nullable=True),
        sa.Column("allergies", sa.JSON(), nullable=True),
        sa.Column("abha_address", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["village_id"], ["villages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patients_abha_id"), "patients", ["abha_id"], unique=True)
    op.create_index(op.f("ix_patients_anonymous_patient_code"), "patients", ["anonymous_patient_code"], unique=True)
    op.create_index(op.f("ix_patients_phone"), "patients", ["phone"], unique=False)
    op.create_index(op.f("ix_patients_village_id"), "patients", ["village_id"], unique=False)
    op.create_index(op.f("ix_patients_created_at"), "patients", ["created_at"], unique=False)
    op.create_index("idx_patients_village_gender", "patients", ["village_id", "gender"], unique=False)

    # 8. care_requests
    op.create_table(
        "care_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("request_number", sa.String(length=50), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("village_id", sa.UUID(), nullable=True),
        sa.Column("origin_facility_id", sa.UUID(), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.Column("assigned_professional_id", sa.UUID(), nullable=True),
        sa.Column("urgency_level", sa.String(length=30), server_default="NORMAL", nullable=False),
        sa.Column("chief_complaint", sa.Text(), nullable=False),
        sa.Column("symptoms", sa.JSON(), nullable=True),
        sa.Column("vitals", sa.JSON(), nullable=True),
        sa.Column("provisional_diagnosis", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="SUBMITTED", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_professional_id"], ["healthcare_professionals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["origin_facility_id"], ["facilities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["village_id"], ["villages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_care_requests_request_number"), "care_requests", ["request_number"], unique=True)
    op.create_index(op.f("ix_care_requests_patient_id"), "care_requests", ["patient_id"], unique=False)
    op.create_index(op.f("ix_care_requests_village_id"), "care_requests", ["village_id"], unique=False)
    op.create_index(op.f("ix_care_requests_origin_facility_id"), "care_requests", ["origin_facility_id"], unique=False)
    op.create_index(op.f("ix_care_requests_created_by_user_id"), "care_requests", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_care_requests_assigned_professional_id"), "care_requests", ["assigned_professional_id"], unique=False)
    op.create_index(op.f("ix_care_requests_urgency_level"), "care_requests", ["urgency_level"], unique=False)
    op.create_index(op.f("ix_care_requests_status"), "care_requests", ["status"], unique=False)
    op.create_index(op.f("ix_care_requests_created_at"), "care_requests", ["created_at"], unique=False)
    op.create_index("idx_care_requests_urgency_status", "care_requests", ["urgency_level", "status"], unique=False)

    # 9. referrals
    op.create_table(
        "referrals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("referral_code", sa.String(length=50), nullable=False),
        sa.Column("care_request_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("origin_facility_id", sa.UUID(), nullable=False),
        sa.Column("destination_facility_id", sa.UUID(), nullable=False),
        sa.Column("referred_by_user_id", sa.UUID(), nullable=True),
        sa.Column("priority", sa.String(length=30), server_default="MEDIUM", nullable=False),
        sa.Column("required_specialty", sa.String(length=100), nullable=True),
        sa.Column("required_capability", sa.String(length=100), nullable=True),
        sa.Column("clinical_summary", sa.Text(), nullable=False),
        sa.Column("transport_mode", sa.String(length=50), nullable=True),
        sa.Column("transport_status", sa.String(length=50), server_default="PENDING", nullable=False),
        sa.Column("status", sa.String(length=50), server_default="INITIATED", nullable=False),
        sa.Column("estimated_transit_minutes", sa.Integer(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("initiated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["care_request_id"], ["care_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["destination_facility_id"], ["facilities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["origin_facility_id"], ["facilities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["referred_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("care_request_id"),
    )
    op.create_index(op.f("ix_referrals_referral_code"), "referrals", ["referral_code"], unique=True)
    op.create_index(op.f("ix_referrals_patient_id"), "referrals", ["patient_id"], unique=False)
    op.create_index(op.f("ix_referrals_origin_facility_id"), "referrals", ["origin_facility_id"], unique=False)
    op.create_index(op.f("ix_referrals_destination_facility_id"), "referrals", ["destination_facility_id"], unique=False)
    op.create_index(op.f("ix_referrals_referred_by_user_id"), "referrals", ["referred_by_user_id"], unique=False)
    op.create_index(op.f("ix_referrals_priority"), "referrals", ["priority"], unique=False)
    op.create_index(op.f("ix_referrals_required_specialty"), "referrals", ["required_specialty"], unique=False)
    op.create_index(op.f("ix_referrals_status"), "referrals", ["status"], unique=False)
    op.create_index(op.f("ix_referrals_created_at"), "referrals", ["created_at"], unique=False)
    op.create_index("idx_referral_status_priority", "referrals", ["status", "priority"], unique=False)
    op.create_index("idx_referral_facilities", "referrals", ["origin_facility_id", "destination_facility_id"], unique=False)

    # 10. referral_events
    op.create_table(
        "referral_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("referral_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("from_status", sa.String(length=50), nullable=True),
        sa.Column("to_status", sa.String(length=50), nullable=False),
        sa.Column("triggered_by_user_id", sa.UUID(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["referral_id"], ["referrals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["triggered_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_referral_events_referral_id"), "referral_events", ["referral_id"], unique=False)
    op.create_index(op.f("ix_referral_events_event_type"), "referral_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_referral_events_triggered_by_user_id"), "referral_events", ["triggered_by_user_id"], unique=False)
    op.create_index(op.f("ix_referral_events_event_timestamp"), "referral_events", ["event_timestamp"], unique=False)

    # 11. follow_ups
    op.create_table(
        "follow_ups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("referral_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("assigned_worker_id", sa.UUID(), nullable=True),
        sa.Column("followup_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="SCHEDULED", nullable=False),
        sa.Column("clinical_notes", sa.Text(), nullable=True),
        sa.Column("recovery_status", sa.String(length=50), nullable=True),
        sa.Column("patient_vitals", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_worker_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["referral_id"], ["referrals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_follow_ups_referral_id"), "follow_ups", ["referral_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_patient_id"), "follow_ups", ["patient_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_assigned_worker_id"), "follow_ups", ["assigned_worker_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_scheduled_date"), "follow_ups", ["scheduled_date"], unique=False)
    op.create_index(op.f("ix_follow_ups_status"), "follow_ups", ["status"], unique=False)
    op.create_index(op.f("ix_follow_ups_created_at"), "follow_ups", ["created_at"], unique=False)
    op.create_index("idx_followup_status_date", "follow_ups", ["status", "scheduled_date"], unique=False)

    # 12. notifications
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=30), server_default="NORMAL", nullable=False),
        sa.Column("reference_entity_type", sa.String(length=50), nullable=True),
        sa.Column("reference_entity_id", sa.UUID(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_index(op.f("ix_notifications_notification_type"), "notifications", ["notification_type"], unique=False)
    op.create_index(op.f("ix_notifications_priority"), "notifications", ["priority"], unique=False)
    op.create_index(op.f("ix_notifications_reference_entity_id"), "notifications", ["reference_entity_id"], unique=False)
    op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"], unique=False)
    op.create_index(op.f("ix_notifications_created_at"), "notifications", ["created_at"], unique=False)
    op.create_index("idx_user_unread_notifications", "notifications", ["user_id", "is_read", "created_at"], unique=False)

    # 13. audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_timestamp"), "audit_logs", ["timestamp"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.create_index("idx_audit_entity_action", "audit_logs", ["entity_type", "action", "timestamp"], unique=False)


def downgrade() -> None:
    # Drop in reverse order of foreign key dependencies
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("follow_ups")
    op.drop_table("referral_events")
    op.drop_table("referrals")
    op.drop_table("care_requests")
    op.drop_table("patients")
    op.drop_table("healthcare_professionals")
    op.drop_table("users")
    op.drop_table("facility_capabilities")
    op.drop_table("villages")
    op.drop_table("facilities")
    op.drop_table("roles")
