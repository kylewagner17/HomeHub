"""Idempotency keys for POST /sync/push — prevents double-apply on mobile retries."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from homehub.db.base import Base


class AppliedMutation(Base):
    """Idempotency log for sync push."""

    __tablename__ = "sync_applied_mutations"

    idempotency_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
