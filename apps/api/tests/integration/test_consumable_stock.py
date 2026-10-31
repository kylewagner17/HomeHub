
def _register(client, email: str, name: str, password: str = "password123"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": name},
    )


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _setup_family(client):
    admin_reg = _register(client, "stock-admin@example.com", "Admin")
    token = admin_reg.json()["access_token"]
    create = client.post(
        "/api/v1/families",
        json={"name": "Stock Family"},
        headers=_auth_headers(token),
    )
    family_id = create.json()["id"]
    client.post(
        f"/api/v1/families/{family_id}/grocery-lists",
        json={"name": "Weekly"},
        headers=_auth_headers(token),
    )
    client.post(
        f"/api/v1/families/{family_id}/grocery-lists",
        json={"name": "Costco"},
        headers=_auth_headers(token),
    )
    return token, family_id


def test_low_stock_adds_to_all_grocery_lists(client):
    token, family_id = _setup_family(client)
    headers = _auth_headers(token)
    create = client.post(
        f"/api/v1/families/{family_id}/maintenance/items",
        json={"category": "items", "item_kind": "consumable", "title": "Toilet paper"},
        headers=headers,
    )
    assert create.status_code == 200
    item_id = create.json()["id"]

    low = client.patch(
        f"/api/v1/families/{family_id}/maintenance/items/{item_id}/stock",
        json={"stock_status": "low"},
        headers=headers,
    )
    assert low.status_code == 200

    lists = client.get(f"/api/v1/families/{family_id}/grocery-lists", headers=headers)
    assert lists.status_code == 200
    pull = client.get(f"/api/v1/sync/pull?family_id={family_id}", headers=headers)
    assert pull.status_code == 200
    for lst in lists.json():
        items = [i for i in pull.json()["grocery_list_items"] if i["list_id"] == lst["id"]]
        names = [i["name"] for i in items if i["deleted_at"] is None]
        assert "Toilet paper" in names

    out = client.patch(
        f"/api/v1/families/{family_id}/maintenance/items/{item_id}/stock",
        json={"stock_status": "out"},
        headers=headers,
    )
    assert out.status_code == 200
    pull = client.get(f"/api/v1/sync/pull?family_id={family_id}", headers=headers)
    linked = [
        i for i in pull.json()["grocery_list_items"] if i["maintenance_item_id"] == item_id
    ]
    assert linked
    assert all(i["urgent_out"] for i in linked)


def test_low_stock_links_existing_grocery_line_by_name(client):
    from uuid import UUID, uuid4

    token, family_id = _setup_family(client)
    headers = _auth_headers(token)
    lists = client.get(f"/api/v1/families/{family_id}/grocery-lists", headers=headers).json()
    list_id = UUID(lists[0]["id"])

    from homehub.main import session_factory
    from homehub.modules.groceries.repository import GroceryListsRepository

    session = session_factory()
    try:
        repo = GroceryListsRepository(session)
        repo.create_item(
            uuid4(),
            list_id,
            UUID(family_id),
            "Paper towels",
            "1",
            False,
            None,
            1,
        )
        session.commit()
    finally:
        session.close()

    create = client.post(
        f"/api/v1/families/{family_id}/maintenance/items",
        json={"category": "items", "item_kind": "consumable", "title": "Paper towels"},
        headers=headers,
    )
    item_id = create.json()["id"]
    low = client.patch(
        f"/api/v1/families/{family_id}/maintenance/items/{item_id}/stock",
        json={"stock_status": "low"},
        headers=headers,
    )
    assert low.status_code == 200

    pull = client.get(f"/api/v1/sync/pull?family_id={family_id}", headers=headers)
    items = [
        i
        for i in pull.json()["grocery_list_items"]
        if i["list_id"] == lists[0]["id"] and i["deleted_at"] is None
    ]
    assert len(items) == 1
    assert items[0]["maintenance_item_id"] == item_id
