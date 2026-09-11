"""Add Care Request fields for Phase 5 (category, service, diagnostics, specialist)

Revision ID: 0002_add_care_request_fields
Revises: 0001_initial_database_foundation
Create Date: 2026-09-12 02:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_add_care_request_fields"
down_revision: Union[str, None] = "0001_initial_database_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Phase 5 Care Request fields
    op.add_column("care_requests", sa.Column("care_category", sa.String(length=50), nullable=True))
    op.add_column("care_requests", sa.Column("required_service", sa.String(length=100), nullable=True))
    op.add_column("care_requests", sa.Column("diagnostic_requirements", sa.JSON(), nullable=True))
    op.add_column("care_requests", sa.Column("specialist_required", sa.Boolean(), server_default=sa.text("false"), nullable=False))

    op.create_index(op.f("ix_care_requests_care_category"), "care_requests", ["care_category"], unique=False)
    op.create_index(op.f("ix_care_requests_required_service"), "care_requests", ["required_service"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_care_requests_required_service"), table_name="care_requests")
    op.drop_index(op.f("ix_care_requests_care_category"), table_name="care_requests")
    op.drop_column("care_requests", "specialist_required")
    op.drop_column("care_requests", "diagnostic_requirements")
    op.drop_column("care_requests", "required_service")
    op.drop_column("care_requests", "care_category")
