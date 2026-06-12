def test_non_trusted_cannot_create_deck(user):
    assert user.post("/decks", json={"name": "x"}).status_code == 403


def test_trusted_creates_private_deck(trusted):
    r = trusted.post("/decks", json={"name": "My Spanish"})
    assert r.status_code == 200
    d = next(x for x in trusted.get("/decks").json()["decks"] if x["name"] == "My Spanish")
    assert d["owner_id"] is not None
    assert d["featured"] is False  # private decks can't be featured


def test_private_deck_hidden_from_others_visible_to_admin(trusted, user, admin):
    did = trusted.post("/decks", json={"name": "secret"}).json()["deck_id"]
    assert "secret" not in [x["name"] for x in user.get("/decks").json()["decks"]]
    assert user.get(f"/decks/{did}").status_code == 404
    assert admin.get(f"/decks/{did}").status_code == 200


def test_owner_edits_and_deletes_own_deck(trusted, user):
    did = trusted.post("/decks", json={"name": "d"}).json()["deck_id"]
    assert trusted.put(f"/decks/{did}", json={"name": "d2"}).status_code == 200
    assert user.put(f"/decks/{did}", json={"name": "x"}).status_code in (403, 404)
    assert trusted.delete(f"/decks/{did}").status_code == 200


def test_trusted_files_private_card_into_own_deck(trusted):
    did = trusted.post("/decks", json={"name": "d"}).json()["deck_id"]
    cid = trusted.post("/cards", json={"front": "f", "back": "b", "deck_id": did}).json()["card_id"]
    card = trusted.get(f"/cards/{cid}").json()["card"]
    assert card["deck_id"] == did and card["owner_id"] is not None


def test_private_card_cannot_go_in_public_deck(trusted, make_deck):
    pub = make_deck(name="pub")  # admin-owned public deck
    assert trusted.post("/cards", json={"front": "f", "back": "b", "deck_id": pub}).status_code == 400


def test_public_card_cannot_go_in_private_deck(trusted, admin):
    priv = trusted.post("/decks", json={"name": "priv"}).json()["deck_id"]
    assert admin.post("/cards", json={"front": "f", "back": "b", "deck_id": priv}).status_code == 400
