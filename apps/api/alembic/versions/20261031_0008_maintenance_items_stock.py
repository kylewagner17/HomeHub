"""maintenance stock status and grocery list links

Revision ID: 0008_maintenance_items_stock
Revises: 0007_maintenance_m5
Create Date: 2026-10-31

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_maintenance_items_stock"
down_revision: str | None = "0007_maintenance_m5"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "maintenance_items",
        sa.Column(
            "stock_status",
            sa.String(length=16),
            nullable=False,
            server_default="in_stock",
        ),
    )
    op.add_column(
        "grocery_list_items",
        sa.Column("maintenance_item_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "grocery_list_items",
        sa.Column("urgent_out", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_foreign_key(
        "fk_grocery_list_items_maintenance_item",
        "grocery_list_items",
        "maintenance_items",
        ["maintenance_item_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_grocery_list_items_maintenance_item_id",
        "grocery_list_items",
        ["maintenance_item_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_grocery_list_items_maintenance_item_id", table_name="grocery_list_items")
    op.drop_constraint("fk_grocery_list_items_maintenance_item", "grocery_list_items", type_="foreignkey")
    op.drop_column("grocery_list_items", "urgent_out")
    op.drop_column("grocery_list_items", "maintenance_item_id")
    op.drop_column("maintenance_items", "stock_status")
