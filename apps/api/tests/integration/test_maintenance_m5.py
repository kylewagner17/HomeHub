from datetime import UTC, datetime, timedelta


def _register(client, email: str, name: str, password: str = "password123"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": name},
    )


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _setup_family(client):
    admin_reg = _register(client, "maint-admin@example.com", "Admin")
    token = admin_reg.json()["access_token"]
    create = client.post(
        "/api/v1/families",
        json={"name": "Maint Family"},
        headers=_auth_headers(token),
    )
    return token, create.json()["id"]


def test_home_filter_complete_reschedules(client):
    token, family_id = _setup_family(client)
    headers = _auth_headers(token)
    due = (datetime.now(UTC) + timedelta(days=30)).isoformat().replace("+00:00", "Z")

    create = client.post(
        f"/api/v1/families/{family_id}/maintenance/items",
        json={
            "category": "home",
            "item_kind": "hvac_filter",
            "title": "Upstairs HVAC",
            "next_due_at": due,
        },
        headers=headers,
    )
    assert create.status_code == 200
    item_id = create.json()["id"]
    assert create.json()["reminder_id"] is not None

    completed_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    next_due = (datetime.now(UTC) + timedelta(days=90)).isoformat().replace("+00:00", "Z")
    done = client.post(
        f"/api/v1/families/{family_id}/maintenance/items/{item_id}/complete",
        json={
            "completed_at": completed_at,
            "next_due_at": next_due,
        },
        headers=headers,
    )
    assert done.status_code == 200
    body = done.json()
    assert body["last_completed_at"] is not None
    assert body["next_due_at"] is not None

    history = client.get(
        f"/api/v1/families/{family_id}/maintenance/history",
        headers=headers,
    )
    assert history.status_code == 200
    assert len(history.json()) >= 1


def test_auto_oil_change_requires_mileage_on_complete(client):
    token, family_id = _setup_family(client)
    headers = _auth_headers(token)
    create = client.post(
        f"/api/v1/families/{family_id}/maintenance/items",
        json={
            "category": "auto",
            "item_kind": "oil_change",
            "title": "Family SUV",
            "interval_miles": 5000,
        },
        headers=headers,
    )
    assert create.status_code == 200
    item_id = create.json()["id"]

    bad = client.post(
        f"/api/v1/families/{family_id}/maintenance/items/{item_id}/complete",
        json={"completed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z")},
        headers=headers,
    )
    assert bad.status_code == 422

    ok = client.post(
        f"/api/v1/families/{family_id}/maintenance/items/{item_id}/complete",
        json={
            "completed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "mileage_at_completion": 40_000,
            "previous_service_mileage": 35_000,
        },
        headers=headers,
    )
    assert ok.status_code == 200
    assert ok.json()["next_due_mileage"] == 45_000
    assert ok.json()["mileage_at_last_service"] == 40_000
