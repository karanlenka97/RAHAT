"""Add Phase 8 Referral Lifecycle & Tracking fields

Revision ID: 0004_add_referral_fields
Revises: 0003_add_facility_and_capability_fields
Create Date: 2026-09-12 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_add_referral_fields"
down_revision: Union[str, None] = "0003_add_facility_and_capability_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new lifecycle columns to referrals
    op.add_column("referrals", sa.Column("parent_referral_id", sa.UUID(), nullable=True))
    op.add_column("referrals", sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("referrals", sa.Column("departed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("referrals", sa.Column("in_service_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("referrals", sa.Column("back_referred_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("referrals", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("referrals", sa.Column("expected_arrival_time", sa.DateTime(timezone=True), nullable=True))
    op.add_column("referrals", sa.Column("rejection_notes", sa.Text(), nullable=True))
    op.add_column("referrals", sa.Column("back_referral_notes", sa.Text(), nullable=True))

    # 2. Make origin_facility_id nullable for village-initiated care requests
    try:
        op.alter_column("referrals", "origin_facility_id", nullable=True)
    except Exception:
        pass

    # 3. Create foreign key and indexes
    try:
        op.create_foreign_key(
            "fk_referrals_parent_referral",
            "referrals",
            "referrals",
            ["parent_referral_id"],
            ["id"],
            ondelete="SET NULL",
        )
    except Exception:
        pass

    try:
        op.create_index(op.f("ix_referrals_parent_referral_id"), "referrals", ["parent_referral_id"], unique=False)
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_constraint("fk_referrals_parent_referral", "referrals", type_="foreignkey")
    except Exception:
        pass
    try:
        op.drop_index(op.f("ix_referrals_parent_referral_id"), table_name="referrals")
    except Exception:
        pass

    op.drop_column("referrals", "back_referral_notes")
    op.drop_column("referrals", "rejection_notes")
    op.drop_column("referrals", "expected_arrival_time")
    op.drop_column("referrals", "closed_at")
    op.drop_column("referrals", "back_referred_at")
    op.drop_column("referrals", "in_service_at")
    op.drop_column("referrals", "departed_at")
    op.drop_column("referrals", "notified_at")
    op.drop_column("referrals", "parent_referral_id")
