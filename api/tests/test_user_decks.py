def _my_deck_id(client):
    return next(d["deck_id"] for d in client.get("/decks").json()["decks"] if d["owner_id"])


def test_non_admin_cannot_create_deck(user, trusted):
    assert user.post("/decks", json={"name": "x"}).status_code == 403
    assert trusted.post("/decks", json={"name": "x"}).status_code == 403  # decks are admin-only now


def test_admin_creates_public_deck(admin):
    r = admin.post("/decks", json={"name": "Public"})
    assert r.status_code == 200
    d = next(x for x in admin.get("/decks").json()["decks"] if x["name"] == "Public")
    assert d["owner_id"] is None


def test_private_card_auto_files_into_my_cards_deck(trusted):
    cid = trusted.post("/cards", json={"front": "f", "back": "b"}).json()["card_id"]
    card = trusted.get(f"/cards/{cid}").json()["card"]
    assert card["owner_id"] is not None
    assert card["deck_id"] is not None  # auto "My Cards" deck
    mine = [d for d in trusted.get("/decks").json()["decks"] if d["owner_id"]]
    assert len(mine) == 1 and mine[0]["name"] == "My Cards"


def test_second_private_card_reuses_the_same_deck(trusted):
    c1 = trusted.post("/cards", json={"front": "a", "back": "b"}).json()["card_id"]
    c2 = trusted.post("/cards", json={"front": "c", "back": "d"}).json()["card_id"]
    d1 = trusted.get(f"/cards/{c1}").json()["card"]["deck_id"]
    d2 = trusted.get(f"/cards/{c2}").json()["card"]["deck_id"]
    assert d1 == d2 and d1 is not None


def test_my_cards_deck_hidden_from_others_visible_to_admin(trusted, user, admin):
    trusted.post("/cards", json={"front": "secret", "back": "x"})
    did = _my_deck_id(trusted)
    assert did not in [d["deck_id"] for d in user.get("/decks").json()["decks"]]
    assert user.get(f"/decks/{did}").status_code == 404
    assert admin.get(f"/decks/{did}").status_code == 200


def test_private_card_ignores_client_deck(trusted, make_deck):
    pub = make_deck(name="pub")  # admin public deck
    cid = trusted.post("/cards", json={"front": "f", "back": "b", "deck_id": pub}).json()["card_id"]
    # the deck_id is ignored — the card lands in "My Cards", not the public deck
    assert trusted.get(f"/cards/{cid}").json()["card"]["deck_id"] != pub


def test_public_card_cannot_go_in_private_deck(trusted, admin):
    trusted.post("/cards", json={"front": "x", "back": "y"})  # creates the My Cards deck
    priv = _my_deck_id(trusted)
    assert admin.post("/cards", json={"front": "p", "back": "q", "deck_id": priv}).status_code == 400
