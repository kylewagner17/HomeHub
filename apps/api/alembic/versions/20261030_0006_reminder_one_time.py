"""rename recurrence none to one_time

Revision ID: 0006_reminder_one_time
Revises: 0005_reminders_m4
Create Date: 2026-10-30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_reminder_one_time"
down_revision: str | None = "0005_reminders_m4"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("UPDATE reminders SET recurrence = 'one_time' WHERE recurrence = 'none'"))


def downgrade() -> None:
    op.execute(sa.text("UPDATE reminders SET recurrence = 'none' WHERE recurrence = 'one_time'"))
