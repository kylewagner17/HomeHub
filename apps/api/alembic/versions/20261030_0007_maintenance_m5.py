"""maintenance items and completion history (M5)

Revision ID: 0007_maintenance_m5
Revises: 0006_reminder_one_time
Create Date: 2026-10-30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_maintenance_m5"
down_revision: str | None = "0006_reminder_one_time"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "maintenance_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("item_kind", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interval_days", sa.Integer(), nullable=True),
        sa.Column("interval_miles", sa.Integer(), nullable=True),
        sa.Column("mileage_at_last_service", sa.Integer(), nullable=True),
        sa.Column("previous_service_mileage", sa.Integer(), nullable=True),
        sa.Column("next_due_mileage", sa.Integer(), nullable=True),
        sa.Column("current_mileage", sa.Integer(), nullable=True),
        sa.Column("reminder_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reminder_id"], ["reminders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_maintenance_items_family_id", "maintenance_items", ["family_id"])
    op.create_index(
        "ix_maintenance_items_family_category",
        "maintenance_items",
        ["family_id", "category"],
    )

    op.create_table(
        "maintenance_completions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mileage_at_completion", sa.Integer(), nullable=True),
        sa.Column("previous_service_mileage", sa.Integer(), nullable=True),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_due_mileage", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["maintenance_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_maintenance_completions_item_id", "maintenance_completions", ["item_id"])
    op.create_index(
        "ix_maintenance_completions_family_id", "maintenance_completions", ["family_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_maintenance_completions_family_id", table_name="maintenance_completions")
    op.drop_index("ix_maintenance_completions_item_id", table_name="maintenance_completions")
    op.drop_table("maintenance_completions")
    op.drop_index("ix_maintenance_items_family_category", table_name="maintenance_items")
    op.drop_index("ix_maintenance_items_family_id", table_name="maintenance_items")
    op.drop_table("maintenance_items")
