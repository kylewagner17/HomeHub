"""grocery lists and sync idempotency

Revision ID: 0002_grocery_sync
Revises: 0001_auth_families
Create Date: 2026-03-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_grocery_sync"
down_revision: str | None = "0001_auth_families"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grocery_lists",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_grocery_lists_family_id"), "grocery_lists", ["family_id"], unique=False)

    op.create_table(
        "sync_applied_mutations",
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("idempotency_key"),
    )
    op.create_index(
        op.f("ix_sync_applied_mutations_family_id"),
        "sync_applied_mutations",
        ["family_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_sync_applied_mutations_family_id"), table_name="sync_applied_mutations")
    op.drop_table("sync_applied_mutations")
    op.drop_index(op.f("ix_grocery_lists_family_id"), table_name="grocery_lists")
    op.drop_table("grocery_lists")
