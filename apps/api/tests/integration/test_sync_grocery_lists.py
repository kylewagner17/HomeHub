from uuid import uuid4


def _register_and_family(client, email: str):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "User"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    fam = client.post("/api/v1/families", json={"name": "Test Family"}, headers=headers)
    return headers, fam.json()["id"]


def test_sync_push_pull_grocery_list_offline_style(client):
    headers, family_id = _register_and_family(client, "sync@example.com")
    list_id = str(uuid4())

    push = client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "family_id": family_id,
            "mutations": [
                {
                    "idempotency_key": "key-create-1",
                    "entity_type": "grocery_list",
                    "operation": "upsert",
                    "entity_id": list_id,
                    "data": {"name": "Offline list", "revision": 1},
                }
            ],
        },
    )
    assert push.status_code == 200
    assert push.json()["results"][0]["status"] == "applied"

    pull = client.get(
        f"/api/v1/sync/pull?family_id={family_id}",
        headers=headers,
    )
    assert pull.status_code == 200
    names = [row["name"] for row in pull.json()["grocery_lists"] if row["deleted_at"] is None]
    assert "Offline list" in names

    dup = client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "family_id": family_id,
            "mutations": [
                {
                    "idempotency_key": "key-create-1",
                    "entity_type": "grocery_list",
                    "operation": "upsert",
                    "entity_id": list_id,
                    "data": {"name": "Offline list", "revision": 1},
                }
            ],
        },
    )
    assert dup.json()["results"][0]["status"] == "duplicate"


def test_sync_ping(client):
    headers, _ = _register_and_family(client, "ping@example.com")
    res = client.get("/api/v1/sync/ping", headers=headers)
    assert res.status_code == 200
    assert res.json()["ok"] is True
