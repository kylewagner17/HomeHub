from datetime import UTC, datetime

SAMPLE_ICS = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:ext-1@test
SUMMARY:Imported meetup
DTSTART:20261101T150000Z
DTEND:20261101T160000Z
END:VEVENT
END:VCALENDAR
"""


def _register(client, email: str, name: str):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": name},
    )


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _family(client, token: str) -> str:
    res = client.post(
        "/api/v1/families",
        json={"name": "Cal Family"},
        headers=_headers(token),
    )
    return res.json()["id"]


def test_calendar_crud_and_ical_import_dedupe(client):
    reg = _register(client, "cal@example.com", "Cal User")
    token = reg.json()["access_token"]
    family_id = _family(client, token)
    headers = _headers(token)
    start = datetime(2026, 11, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 11, 30, 23, 59, tzinfo=UTC)

    create = client.post(
        f"/api/v1/families/{family_id}/calendar/events",
        headers=headers,
        json={
            "title": "Family dinner",
            "starts_at": "2026-11-05T18:00:00Z",
            "ends_at": "2026-11-05T20:00:00Z",
            "visibility": "family",
        },
    )
    assert create.status_code == 200
    event_id = create.json()["id"]

    listed = client.get(
        f"/api/v1/families/{family_id}/calendar/events",
        headers=headers,
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    patch = client.patch(
        f"/api/v1/families/{family_id}/calendar/events/{event_id}",
        headers=headers,
        json={"title": "Family dinner (updated)"},
    )
    assert patch.status_code == 200
    assert patch.json()["title"] == "Family dinner (updated)"

    imp = client.post(
        f"/api/v1/families/{family_id}/calendar/import/ical",
        headers=headers,
        json={"ics_text": SAMPLE_ICS},
    )
    assert imp.status_code == 200
    assert imp.json()["imported"] == 1

    imp2 = client.post(
        f"/api/v1/families/{family_id}/calendar/import/ical",
        headers=headers,
        json={"ics_text": SAMPLE_ICS},
    )
    assert imp2.json()["skipped_duplicates"] == 1
    assert imp2.json()["imported"] == 0

    listed2 = client.get(
        f"/api/v1/families/{family_id}/calendar/events",
        headers=headers,
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    assert len(listed2.json()) == 2

    export = client.get(
        f"/api/v1/families/{family_id}/calendar/export/ical",
        headers=headers,
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    assert export.status_code == 200
    assert "BEGIN:VCALENDAR" in export.text

    delete = client.delete(
        f"/api/v1/families/{family_id}/calendar/events/{event_id}",
        headers=headers,
    )
    assert delete.status_code == 204


def test_import_does_not_overwrite_existing_homehub_event(client):
    reg = _register(client, "cal-dedupe@example.com", "User")
    token = reg.json()["access_token"]
    family_id = _family(client, token)
    headers = _headers(token)

    client.post(
        f"/api/v1/families/{family_id}/calendar/events",
        headers=headers,
        json={
            "title": "Imported meetup",
            "starts_at": "2026-11-01T15:00:00Z",
            "ends_at": "2026-11-01T16:00:00Z",
            "visibility": "family",
        },
    )

    imp = client.post(
        f"/api/v1/families/{family_id}/calendar/import/ical",
        headers=headers,
        json={"ics_text": SAMPLE_ICS},
    )
    assert imp.json()["imported"] == 0
    assert imp.json()["skipped_duplicates"] == 1

    start = datetime(2026, 11, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 11, 2, 0, 0, tzinfo=UTC)
    listed = client.get(
        f"/api/v1/families/{family_id}/calendar/events",
        headers=headers,
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    assert len(listed.json()) == 1
