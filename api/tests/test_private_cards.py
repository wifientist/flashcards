def test_untrusted_user_cannot_create(user):
    assert user.post("/cards", json={"front": "a", "back": "b"}).status_code == 403


def test_admin_card_is_public(admin, make_card):
    cid = make_card(front="pub")
    assert admin.get(f"/cards/{cid}").json()["card"]["owner_id"] is None


def test_trusted_creates_private_card(trusted):
    r = trusted.post("/cards", json={"front": "p", "back": "q"})
    assert r.status_code == 200
    mine = trusted.get("/cards?mine=1").json()["cards"]
    assert [c["front"] for c in mine] == ["p"]
    assert mine[0]["owner_id"] is not None
    assert mine[0]["deck_id"] is not None  # auto-filed into "My Cards"


def test_private_card_hidden_from_others_visible_to_admin(trusted, user, admin):
    cid = trusted.post("/cards", json={"front": "secret", "back": "x"}).json()["card_id"]
    # other users don't see it in the list or by id
    assert "secret" not in [c["front"] for c in user.get("/cards").json()["cards"]]
    assert user.get(f"/cards/{cid}").status_code == 404
    # admins can (so they can appropriate it)
    assert admin.get(f"/cards/{cid}").status_code == 200


def test_owner_can_edit_and_delete_own(trusted, user):
    cid = trusted.post("/cards", json={"front": "mine", "back": "x"}).json()["card_id"]
    assert trusted.put(f"/cards/{cid}", json={"front": "mine2"}).status_code == 200
    assert user.put(f"/cards/{cid}", json={"front": "nope"}).status_code in (403, 404)
    assert user.delete(f"/cards/{cid}").status_code in (403, 404)
    assert trusted.delete(f"/cards/{cid}").status_code == 200


def test_admin_can_create_private_card(admin):
    cid = admin.post("/cards", json={"front": "mine", "back": "x", "private": True}).json()["card_id"]
    assert admin.get(f"/cards/{cid}").json()["card"]["owner_id"] is not None
    assert "mine" in [c["front"] for c in admin.get("/cards?mine=1").json()["cards"]]


def test_admin_default_card_is_public(admin):
    cid = admin.post("/cards", json={"front": "app", "back": "x"}).json()["card_id"]
    assert admin.get(f"/cards/{cid}").json()["card"]["owner_id"] is None


def test_trusted_private_flag_cannot_make_public(trusted):
    cid = trusted.post("/cards", json={"front": "p", "back": "x", "private": False}).json()["card_id"]
    mine = trusted.get("/cards?mine=1").json()["cards"]
    assert any(c["card_id"] == cid for c in mine)  # still private


def test_private_card_not_leaked_by_export(trusted, user):
    trusted.post("/cards", json={"front": "secret", "back": "x"})
    assert "secret" not in user.get("/export/cards?format=csv").text


def test_private_card_not_leaked_by_status_new(trusted, user, make_card):
    trusted.post("/cards", json={"front": "secret", "back": "x"})
    make_card(front="pub")
    fronts = [c["front"] for c in user.get("/cards/by-status/new").json()["cards"]]
    assert "secret" not in fronts and "pub" in fronts


def test_cannot_review_or_track_invisible_card(trusted, user):
    cid = trusted.post("/cards", json={"front": "secret", "back": "x"}).json()["card_id"]
    assert user.post(f"/cards/{cid}/review", json={"rating": "good"}).status_code == 404
    assert user.put(f"/cards/{cid}/progress", json={"flagged": True}).status_code == 404


def test_private_card_shows_owner_email_to_admin(trusted, admin):
    trusted.post("/cards", json={"front": "p", "back": "x"})
    priv = next(c for c in admin.get("/cards").json()["cards"] if c["front"] == "p")
    assert priv["owner_email"] == "trusted@test.com"


def test_admin_can_audit_a_users_cards(trusted, admin):
    trusted.post("/cards", json={"front": "p1", "back": "x"})
    trusted.post("/cards", json={"front": "p2", "back": "y"})
    uid = next(u["user_id"] for u in admin.get("/auth/users").json()["users"]
               if u["email"] == "trusted@test.com")
    fronts = {c["front"] for c in admin.get(f"/cards?owner={uid}").json()["cards"]}
    assert {"p1", "p2"} <= fronts


def test_admin_copy_into_public_deck(trusted, admin, user, make_deck):
    dest = make_deck(name="dest")
    cid = trusted.post("/cards", json={"front": "priv", "back": "x"}).json()["card_id"]
    new_id = admin.post(f"/cards/{cid}/copy", json={"deck_id": dest}).json()["card_id"]
    card = user.get(f"/cards/{new_id}").json()["card"]  # public -> visible to anyone
    assert card["deck_id"] == dest and card["owner_id"] is None


def test_admin_copy_private_to_public_keeps_original(trusted, admin, user):
    cid = trusted.post("/cards", json={"front": "priv", "back": "x"}).json()["card_id"]
    new_id = admin.post(f"/cards/{cid}/copy").json()["card_id"]
    # the copy is public
    assert admin.get(f"/cards/{new_id}").json()["card"]["owner_id"] is None
    assert user.get(f"/cards/{new_id}").status_code == 200  # visible to everyone
    # the original stays private to the owner
    assert user.get(f"/cards/{cid}").status_code == 404
