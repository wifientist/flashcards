def test_untrusted_user_cannot_create(user):
    assert user.post("/cards", json={"front": "a", "back": "b"}).status_code == 403


def test_admin_card_is_public(admin, make_card):
    cid = make_card(front="pub")
    assert admin.get(f"/cards/{cid}").json()["card"]["owner_id"] is None


def test_trusted_creates_private_card(trusted):
    r = trusted.post("/cards", json={"front": "p", "back": "q", "deck_id": None})
    assert r.status_code == 200
    mine = trusted.get("/cards?mine=1").json()["cards"]
    assert [c["front"] for c in mine] == ["p"]
    assert mine[0]["owner_id"] is not None
    assert mine[0]["deck_id"] is None  # private cards are deck-less


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


def test_admin_copy_private_to_public_keeps_original(trusted, admin, user):
    cid = trusted.post("/cards", json={"front": "priv", "back": "x"}).json()["card_id"]
    new_id = admin.post(f"/cards/{cid}/copy").json()["card_id"]
    # the copy is public
    assert admin.get(f"/cards/{new_id}").json()["card"]["owner_id"] is None
    assert user.get(f"/cards/{new_id}").status_code == 200  # visible to everyone
    # the original stays private to the owner
    assert user.get(f"/cards/{cid}").status_code == 404
