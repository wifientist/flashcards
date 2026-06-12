def test_non_admin_cannot_create_deck(user):
    assert user.post("/decks", json={"name": "x"}).status_code == 403


def test_create_deck_and_card_count(admin, make_deck, make_card):
    deck = make_deck(name="French", description="vocab")
    make_card(deck_id=deck)
    decks = {d["deck_id"]: d for d in admin.get("/decks").json()["decks"]}
    assert decks[deck]["name"] == "French"
    assert decks[deck]["card_count"] == 1


def test_create_card_with_bad_deck_400(admin):
    assert admin.post("/cards", json={"front": "a", "back": "b", "deck_id": "nope"}).status_code == 400


def test_filter_cards_by_deck(admin, make_deck, make_card):
    deck = make_deck()
    make_card(front="in", deck_id=deck)
    make_card(front="out")
    cards = admin.get(f"/cards?deck_id={deck}").json()["cards"]
    assert [c["front"] for c in cards] == ["in"]


def test_delete_deck_unfiles_cards(admin, make_deck, make_card):
    deck = make_deck()
    cid = make_card(deck_id=deck)
    assert admin.delete(f"/decks/{deck}").status_code == 200
    # card survives, now unfiled
    card = admin.get(f"/cards/{cid}").json()["card"]
    assert card["deck_id"] is None


def test_update_deck(admin, make_deck):
    deck = make_deck(name="old")
    assert admin.put(f"/decks/{deck}", json={"name": "new"}).status_code == 200
    assert admin.get(f"/decks/{deck}").json()["deck"]["name"] == "new"
