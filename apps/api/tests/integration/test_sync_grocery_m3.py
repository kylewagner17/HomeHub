from uuid import uuid4


def _register_and_family(client, email: str):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "User"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    fam = client.post("/api/v1/families", json={"name": "Test Family"}, headers=headers)
    return headers, fam.json()["id"], fam.json()["invite_code"]


def test_partner_sees_list_item_via_pull(client):
    headers_a, family_id, invite = _register_and_family(client, "alice@example.com")
    reg_b = client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "password": "password123", "display_name": "Bob"},
    )
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}
    join = client.post("/api/v1/families/join", json={"invite_code": invite}, headers=headers_b)
    assert join.status_code == 200

    list_id = str(uuid4())
    item_id = str(uuid4())
    client.post(
        "/api/v1/sync/push",
        headers=headers_a,
        json={
            "family_id": family_id,
            "mutations": [
                {
                    "idempotency_key": "m3-list-01",
                    "entity_type": "grocery_list",
                    "operation": "upsert",
                    "entity_id": list_id,
                    "data": {"name": "Weekly", "revision": 1},
                },
                {
                    "idempotency_key": "m3-item-01",
                    "entity_type": "grocery_list_item",
                    "operation": "upsert",
                    "entity_id": item_id,
                    "data": {
                        "name": "Milk",
                        "list_id": list_id,
                        "quantity": "1",
                        "checked": False,
                        "revision": 1,
                    },
                },
            ],
        },
    )

    pull = client.get(f"/api/v1/sync/pull?family_id={family_id}", headers=headers_b)
    assert pull.status_code == 200
    body = pull.json()
    assert any(i["name"] == "Milk" for i in body["grocery_list_items"])


def test_sync_push_merges_duplicate_item_names(client):
    headers, family_id, _ = _register_and_family(client, "merge@example.com")
    list_id = str(uuid4())
    client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "family_id": family_id,
            "mutations": [
                {
                    "idempotency_key": "merge-list",
                    "entity_type": "grocery_list",
                    "operation": "upsert",
                    "entity_id": list_id,
                    "data": {"name": "Shop", "revision": 1},
                }
            ],
        },
    )
    first_id = str(uuid4())
    second_id = str(uuid4())
    client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "family_id": family_id,
            "mutations": [
                {
                    "idempotency_key": "merge-item-1",
                    "entity_type": "grocery_list_item",
                    "operation": "upsert",
                    "entity_id": first_id,
                    "data": {
                        "name": "Milk",
                        "list_id": list_id,
                        "quantity": "1",
                        "checked": False,
                        "revision": 1,
                    },
                },
                {
                    "idempotency_key": "merge-item-2",
                    "entity_type": "grocery_list_item",
                    "operation": "upsert",
                    "entity_id": second_id,
                    "data": {
                        "name": "milk",
                        "list_id": list_id,
                        "quantity": "1",
                        "checked": False,
                        "revision": 1,
                    },
                },
            ],
        },
    )
    pull = client.get(f"/api/v1/sync/pull?family_id={family_id}", headers=headers)
    milk_rows = [
        row
        for row in pull.json()["grocery_list_items"]
        if row["name"].lower() == "milk" and row["deleted_at"] is None
    ]
    assert len(milk_rows) == 1
    assert milk_rows[0]["quantity"] == "2"


def test_estimate_with_store_price(client):
    headers, family_id, _ = _register_and_family(client, "est@example.com")
    list_id = str(uuid4())
    store_id = str(uuid4())
    price_id = str(uuid4())
    item_id = str(uuid4())

    client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "family_id": family_id,
            "mutations": [
                {
                    "idempotency_key": "est-list",
                    "entity_type": "grocery_list",
                    "operation": "upsert",
                    "entity_id": list_id,
                    "data": {"name": "Shop", "revision": 1},
                },
                {
                    "idempotency_key": "est-store",
                    "entity_type": "grocery_store",
                    "operation": "upsert",
                    "entity_id": store_id,
                    "data": {"name": "Local Mart", "revision": 1},
                },
                {
                    "idempotency_key": "est-price",
                    "entity_type": "grocery_store_price",
                    "operation": "upsert",
                    "entity_id": price_id,
                    "data": {
                        "store_id": store_id,
                        "item_name": "Milk",
                        "price_cents": 499,
                        "revision": 1,
                    },
                },
                {
                    "idempotency_key": "est-item",
                    "entity_type": "grocery_list_item",
                    "operation": "upsert",
                    "entity_id": item_id,
                    "data": {
                        "name": "Milk",
                        "list_id": list_id,
                        "quantity": "2",
                        "checked": False,
                        "revision": 1,
                    },
                },
            ],
        },
    )

    res = client.get(
        f"/api/v1/families/{family_id}/grocery-lists/{list_id}/estimate?store_id={store_id}",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["total_cents"] == 998
