"""grocery store optional external metadata (unused for pricing)

Revision ID: 0004_grocery_store_external
Revises: 0003_grocery_m3
Create Date: 2026-10-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_grocery_store_external"
down_revision: str | None = "0003_grocery_m3"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("grocery_stores", sa.Column("external_provider", sa.String(length=32), nullable=True))
    op.add_column("grocery_stores", sa.Column("external_store_id", sa.String(length=64), nullable=True))
    op.add_column("grocery_stores", sa.Column("address_line", sa.String(length=255), nullable=True))
    op.create_index(
        "ix_grocery_stores_family_external",
        "grocery_stores",
        ["family_id", "external_provider", "external_store_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_grocery_stores_family_external", table_name="grocery_stores")
    op.drop_column("grocery_stores", "address_line")
    op.drop_column("grocery_stores", "external_store_id")
    op.drop_column("grocery_stores", "external_provider")
