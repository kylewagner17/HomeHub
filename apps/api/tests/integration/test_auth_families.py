def _register(client, email: str, name: str, password: str = "password123"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": name},
    )


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_two_users_one_family_roles_and_cross_family_denied(client):
    admin_reg = _register(client, "admin@example.com", "Admin")
    assert admin_reg.status_code == 200
    admin_token = admin_reg.json()["access_token"]

    create = client.post(
        "/api/v1/families",
        json={"name": "Smith Family"},
        headers=_auth_headers(admin_token),
    )
    assert create.status_code == 200
    family = create.json()
    invite = family["invite_code"]
    family_id = family["id"]

    member_reg = _register(client, "child@example.com", "Child")
    assert member_reg.status_code == 200
    member_token = member_reg.json()["access_token"]

    join = client.post(
        "/api/v1/families/join",
        json={"invite_code": invite},
        headers=_auth_headers(member_token),
    )
    assert join.status_code == 200

    admin_me = client.get("/api/v1/auth/me", headers=_auth_headers(admin_token))
    member_me = client.get("/api/v1/auth/me", headers=_auth_headers(member_token))
    assert admin_me.json()["memberships"][0]["role"] == "admin"
    assert member_me.json()["memberships"][0]["role"] == "member"

    other_reg = _register(client, "outsider@example.com", "Outsider")
    outsider_token = other_reg.json()["access_token"]
    denied = client.get(f"/api/v1/families/{family_id}", headers=_auth_headers(outsider_token))
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FORBIDDEN"


def test_login_invalid_credentials(client):
    _register(client, "user@example.com", "User")
    bad = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrongpass"},
    )
    assert bad.status_code == 401
