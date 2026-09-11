"""Add Phase 6 Facility and FacilityCapability fields

Revision ID: 0003_add_facility_and_capability_fields
Revises: 0002_add_care_request_fields
Create Date: 2026-09-12 02:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_add_facility_and_capability_fields"
down_revision: Union[str, None] = "0002_add_care_request_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add operating_hours to facilities if not present
    op.add_column("facilities", sa.Column("operating_hours", sa.String(length=100), server_default="24x7", nullable=True))

    # 2. Add Phase 6 Capability fields
    op.add_column("facility_capabilities", sa.Column("service_name", sa.String(length=150), nullable=True))
    op.add_column("facility_capabilities", sa.Column("service_category", sa.String(length=100), nullable=True))
    op.add_column("facility_capabilities", sa.Column("available", sa.Boolean(), server_default=sa.text("true"), nullable=False))
    op.add_column("facility_capabilities", sa.Column("availability_status", sa.String(length=50), server_default="AVAILABLE", nullable=False))
    op.add_column("facility_capabilities", sa.Column("capacity", sa.Integer(), server_default="50", nullable=False))
    op.add_column("facility_capabilities", sa.Column("current_load", sa.Integer(), server_default="0", nullable=False))
    op.add_column("facility_capabilities", sa.Column("specialist_required", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("facility_capabilities", sa.Column("diagnostic_required", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("facility_capabilities", sa.Column("operating_hours", sa.String(length=100), server_default="24x7", nullable=True))

    # 3. Create indexes
    op.create_index(op.f("ix_facility_capabilities_service_category"), "facility_capabilities", ["service_category"], unique=False)
    op.create_index(op.f("ix_facility_capabilities_service_name"), "facility_capabilities", ["service_name"], unique=False)
    op.create_index(op.f("ix_facility_capabilities_availability_status"), "facility_capabilities", ["availability_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_facility_capabilities_availability_status"), table_name="facility_capabilities")
    op.drop_index(op.f("ix_facility_capabilities_service_name"), table_name="facility_capabilities")
    op.drop_index(op.f("ix_facility_capabilities_service_category"), table_name="facility_capabilities")

    op.drop_column("facility_capabilities", "operating_hours")
    op.drop_column("facility_capabilities", "diagnostic_required")
    op.drop_column("facility_capabilities", "specialist_required")
    op.drop_column("facility_capabilities", "current_load")
    op.drop_column("facility_capabilities", "capacity")
    op.drop_column("facility_capabilities", "availability_status")
    op.drop_column("facility_capabilities", "available")
    op.drop_column("facility_capabilities", "service_category")
    op.drop_column("facility_capabilities", "service_name")

    op.drop_column("facilities", "operating_hours")
