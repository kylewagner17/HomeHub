"""Best-effort FCM legacy HTTP when FCM_SERVER_KEY is configured."""

import logging
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from homehub.config import Settings
from homehub.modules.auth.repository import AuthRepository

logger = logging.getLogger(__name__)


def send_push_to_users(
    session: Session,
    settings: Settings,
    user_ids: list[UUID],
    title: str,
    body: str | None,
) -> None:
    if not settings.fcm_server_key:
        return
    auth_repo = AuthRepository(session)
    tokens: list[str] = []
    for user_id in user_ids:
        tokens.extend(auth_repo.list_push_tokens_for_user(user_id))
    if not tokens:
        return
    payload = {
        "registration_ids": tokens,
        "notification": {"title": title, "body": body or title},
    }
    try:
        response = httpx.post(
            "https://fcm.googleapis.com/fcm/send",
            json=payload,
            headers={
                "Authorization": f"key={settings.fcm_server_key}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )
        if response.status_code >= 400:
            logger.warning("FCM dispatch failed status=%s", response.status_code)
    except httpx.HTTPError:
        logger.exception("FCM dispatch error")
