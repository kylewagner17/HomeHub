from datetime import UTC, datetime, timedelta

from homehub.main import session_factory
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.reminders.repository import RemindersRepository
from homehub.modules.reminders.service import RemindersService


def _register(client, email: str, name: str, password: str = "password123"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": name},
    )


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _setup_family(client):
    admin_reg = _register(client, "reminder-admin@example.com", "Admin")
    token = admin_reg.json()["access_token"]
    create = client.post(
        "/api/v1/families",
        json={"name": "Reminder Family"},
        headers=_auth_headers(token),
    )
    family_id = create.json()["id"]
    return token, family_id


def test_reminder_crud_fire_and_history(client):
    token, family_id = _setup_family(client)
    headers = _auth_headers(token)
    due = (datetime.now(UTC) - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")

    create = client.post(
        f"/api/v1/families/{family_id}/reminders",
        json={"title": "Take bins out", "recurrence": "one_time", "next_fire_at": due},
        headers=headers,
    )
    assert create.status_code == 200
    reminder_id = create.json()["id"]

    session = session_factory()
    try:
        service = RemindersService(RemindersRepository(session), FamiliesRepository(session))
        count = service.process_due_reminders(datetime.now(UTC))
        session.commit()
        assert count == 1
    finally:
        session.close()

    history = client.get(
        f"/api/v1/families/{family_id}/reminders/history",
        headers=headers,
    )
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["title"] == "Take bins out"

    notifications = client.get("/api/v1/notifications", headers=headers)
    assert notifications.status_code == 200
    items = notifications.json()
    assert len(items) >= 1
    assert items[0]["title"] == "Take bins out"

    updated = client.get(f"/api/v1/families/{family_id}/reminders", headers=headers)
    row = next(r for r in updated.json() if r["id"] == reminder_id)
    assert row["enabled"] is False


def test_reminder_denied_for_outsider(client):
    token, family_id = _setup_family(client)
    outsider = _register(client, "outsider-rem@example.com", "Out")
    outsider_token = outsider.json()["access_token"]
    due = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    denied = client.post(
        f"/api/v1/families/{family_id}/reminders",
        json={"title": "Nope", "next_fire_at": due},
        headers=_auth_headers(outsider_token),
    )
    assert denied.status_code == 403
