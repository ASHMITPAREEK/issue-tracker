def test_register_success(client):
    resp = client.post(
        "/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert "hashed_password" not in body


def test_register_duplicate_email(client):
    payload = {"name": "Alice", "email": "dup@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 409
    assert "error" in resp.json()


def test_register_invalid_email(client):
    resp = client.post(
        "/auth/register",
        json={"name": "Alice", "email": "not-an-email", "password": "password123"},
    )
    assert resp.status_code == 422


def test_register_password_too_short(client):
    resp = client.post(
        "/auth/register",
        json={"name": "Alice", "email": "shortpw@example.com", "password": "short"},
    )
    assert resp.status_code == 422


def test_register_missing_fields(client):
    resp = client.post("/auth/register", json={"email": "missing@example.com"})
    assert resp.status_code == 422


def test_login_success(client):
    client.post(
        "/auth/register",
        json={"name": "Bob", "email": "bob@example.com", "password": "password123"},
    )
    resp = client.post("/auth/login", json={"email": "bob@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"name": "Bob", "email": "bob2@example.com", "password": "password123"},
    )
    resp = client.post("/auth/login", json={"email": "bob2@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post("/auth/login", json={"email": "nope@example.com", "password": "password123"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_with_valid_token(client, auth_headers):
    headers = auth_headers()
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@example.com"


def test_logout_requires_auth(client):
    resp = client.post("/auth/logout")
    assert resp.status_code == 401


def test_logout_with_valid_token(client, auth_headers):
    headers = auth_headers()
    resp = client.post("/auth/logout", headers=headers)
    assert resp.status_code == 200


def test_invalid_token_rejected(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
