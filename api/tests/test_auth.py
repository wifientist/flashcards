def test_health(client):
    assert client.get("/auth/health").json() == {"status": "ok"}


def test_whoami_unauthenticated_is_guest(client):
    data = client.get("/auth/whoami").json()
    assert data["authenticated"] is False
    assert data["roles"] == ["guest"]


def test_public_registration_is_disabled(client):
    # Self-signup is gone; user creation is admin-only.
    assert client.post("/auth/register", json={"email": "x@test.com", "password": "pw1234567"}).status_code == 404


def test_login_bad_password_401(admin, client):
    admin.post("/auth/users", json={"email": "x@test.com", "password": "rightpw123"})
    r = client.post("/auth/login", json={"email": "x@test.com", "password": "wrongpw123"})
    assert r.status_code == 401


def test_login_rate_limited(admin, client):
    admin.post("/auth/users", json={"email": "rl@test.com", "password": "rightpw123"})
    # Limit is 10 per 5 min; the 11th attempt should be throttled.
    codes = [
        client.post("/auth/login", json={"email": "rl@test.com", "password": "nope"}).status_code
        for _ in range(11)
    ]
    assert 429 in codes


# --- admin user creation ---------------------------------------------------

def test_non_admin_cannot_create_user(client, user):
    body = {"email": "new@test.com", "password": "pw1234567"}
    assert client.post("/auth/users", json=body).status_code == 401   # anonymous
    assert user.post("/auth/users", json=body).status_code == 403     # regular user


def test_admin_creates_user_with_roles(admin, client):
    r = admin.post("/auth/users", json={
        "email": "trusted2@test.com", "password": "pw1234567", "roles": ["user", "trusted"],
    })
    assert r.status_code == 200
    # the new user appears with the right roles and can log in
    row = next(u for u in admin.get("/auth/users").json()["users"] if u["email"] == "trusted2@test.com")
    assert set(row["roles"]) == {"user", "trusted"}
    assert client.post("/auth/login", json={"email": "trusted2@test.com", "password": "pw1234567"}).status_code == 200


def test_admin_create_duplicate_email_400(admin):
    body = {"email": "dup@test.com", "password": "pw1234567"}
    assert admin.post("/auth/users", json=body).status_code == 200
    assert admin.post("/auth/users", json=body).status_code == 400


# --- admin self-guards -----------------------------------------------------

def test_admin_cannot_remove_own_admin(admin):
    me = admin.get("/auth/whoami").json()
    r = admin.put(f"/auth/users/{me['user_id']}/roles", json={"roles": ["user"]})
    assert r.status_code == 400


def test_admin_cannot_deactivate_self(admin):
    me = admin.get("/auth/whoami").json()
    assert admin.delete(f"/auth/users/{me['user_id']}").status_code == 400


def test_deactivate_blocks_login_then_reactivate(admin, client):
    admin.post("/auth/users", json={"email": "victim@test.com", "password": "pw1234567"})
    uid = next(u["user_id"] for u in admin.get("/auth/users").json()["users"]
               if u["email"] == "victim@test.com")

    assert admin.delete(f"/auth/users/{uid}").status_code == 200
    assert client.post("/auth/login", json={"email": "victim@test.com", "password": "pw1234567"}).status_code == 401

    assert admin.post(f"/auth/users/{uid}/activate").status_code == 200
    assert client.post("/auth/login", json={"email": "victim@test.com", "password": "pw1234567"}).status_code == 200


def test_admin_sessions_include_email(admin):
    sessions = admin.get("/admin/sessions").json()["sessions"]
    assert any(s.get("email") == "admin@test.com" for s in sessions)


def test_admin_only_user_list(client, admin, user):
    assert client.get("/auth/users").status_code == 401      # unauthenticated
    assert user.get("/auth/users").status_code == 403        # regular user
    resp = admin.get("/auth/users")
    assert resp.status_code == 200
    # never leak password hashes
    assert all("hashed_password" not in u for u in resp.json()["users"])
