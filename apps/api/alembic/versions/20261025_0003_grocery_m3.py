"""grocery M3 items staples stores prices

Revision ID: 0003_grocery_m3
Revises: 0002_grocery_sync
Create Date: 2026-10-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_grocery_m3"
down_revision: str | None = "0002_grocery_sync"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grocery_stores",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_grocery_stores_family_id"), "grocery_stores", ["family_id"], unique=False)

    op.create_table(
        "grocery_staples",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_grocery_staples_family_id"), "grocery_staples", ["family_id"], unique=False)

    op.add_column(
        "grocery_lists",
        sa.Column("selected_store_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_grocery_lists_selected_store_id",
        "grocery_lists",
        "grocery_stores",
        ["selected_store_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "grocery_list_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("list_id", sa.UUID(), nullable=False),
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("quantity", sa.String(length=32), server_default="1", nullable=False),
        sa.Column("checked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("staple_id", sa.UUID(), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["list_id"], ["grocery_lists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["staple_id"], ["grocery_staples.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_grocery_list_items_family_id"), "grocery_list_items", ["family_id"], unique=False
    )
    op.create_index(
        op.f("ix_grocery_list_items_list_id"), "grocery_list_items", ["list_id"], unique=False
    )

    op.create_table(
        "grocery_store_prices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("store_id", sa.UUID(), nullable=False),
        sa.Column("item_name", sa.String(length=120), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], ["grocery_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_grocery_store_prices_family_id"), "grocery_store_prices", ["family_id"], unique=False
    )
    op.create_index(
        op.f("ix_grocery_store_prices_store_id"), "grocery_store_prices", ["store_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_grocery_store_prices_store_id"), table_name="grocery_store_prices")
    op.drop_index(op.f("ix_grocery_store_prices_family_id"), table_name="grocery_store_prices")
    op.drop_table("grocery_store_prices")
    op.drop_index(op.f("ix_grocery_list_items_list_id"), table_name="grocery_list_items")
    op.drop_index(op.f("ix_grocery_list_items_family_id"), table_name="grocery_list_items")
    op.drop_table("grocery_list_items")
    op.drop_constraint("fk_grocery_lists_selected_store_id", "grocery_lists", type_="foreignkey")
    op.drop_column("grocery_lists", "selected_store_id")
    op.drop_index(op.f("ix_grocery_staples_family_id"), table_name="grocery_staples")
    op.drop_table("grocery_staples")
    op.drop_index(op.f("ix_grocery_stores_family_id"), table_name="grocery_stores")
    op.drop_table("grocery_stores")
