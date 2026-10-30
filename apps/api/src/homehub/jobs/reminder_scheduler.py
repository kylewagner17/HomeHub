"""In-process reminder scheduler (ADR-006)."""

import logging
from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import sessionmaker

from homehub.config import get_settings
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.reminders.repository import RemindersRepository
from homehub.modules.reminders.service import RemindersService

logger = logging.getLogger(__name__)


def _run_tick(session_factory: sessionmaker) -> None:
    session = session_factory()
    try:
        service = RemindersService(RemindersRepository(session), FamiliesRepository(session))
        count = service.process_due_reminders(datetime.now(UTC))
        session.commit()
        if count:
            logger.info("Processed %s due reminder(s)", count)
    except Exception:
        session.rollback()
        logger.exception("Reminder scheduler tick failed")
    finally:
        session.close()


def start_reminder_scheduler(session_factory: sessionmaker) -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _run_tick,
        "interval",
        seconds=settings.reminder_scheduler_interval_seconds,
        args=[session_factory],
        id="reminder_fire",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Reminder scheduler started (interval=%ss)",
        settings.reminder_scheduler_interval_seconds,
    )
    return scheduler
