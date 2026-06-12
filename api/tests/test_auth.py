def test_health(client):
    assert client.get("/auth/health").json() == {"status": "ok"}


def test_whoami_unauthenticated_is_guest(client):
    data = client.get("/auth/whoami").json()
    assert data["authenticated"] is False
    assert data["roles"] == ["guest"]


def test_register_ignores_client_roles(client):
    # Attempt privilege escalation via the request body.
    client.post("/auth/register", json={
        "email": "sneaky@test.com", "password": "pw1234567", "roles": ["admin"],
    })
    client.post("/auth/login", json={"email": "sneaky@test.com", "password": "pw1234567"})
    assert client.get("/auth/whoami").json()["roles"] == ["user"]


def test_register_duplicate_email_400(client):
    body = {"email": "dup@test.com", "password": "pw1234567"}
    assert client.post("/auth/register", json=body).status_code == 200
    assert client.post("/auth/register", json=body).status_code == 400


def test_login_bad_password_401(client):
    client.post("/auth/register", json={"email": "x@test.com", "password": "rightpw123"})
    r = client.post("/auth/login", json={"email": "x@test.com", "password": "wrongpw123"})
    assert r.status_code == 401


def test_login_rate_limited(client):
    client.post("/auth/register", json={"email": "rl@test.com", "password": "rightpw123"})
    # Limit is 10 per 5 min; the 11th attempt should be throttled.
    codes = [
        client.post("/auth/login", json={"email": "rl@test.com", "password": "nope"}).status_code
        for _ in range(11)
    ]
    assert 429 in codes


def test_admin_only_user_list(client, admin, user):
    assert client.get("/auth/users").status_code == 401      # unauthenticated
    assert user.get("/auth/users").status_code == 403        # regular user
    resp = admin.get("/auth/users")
    assert resp.status_code == 200
    # never leak password hashes
    assert all("hashed_password" not in u for u in resp.json()["users"])
