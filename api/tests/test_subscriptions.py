"""Deck subscriptions — the study universe. Users subscribe to decks; the queue
and card list scope to subscribed decks (client-side, via deck_ids)."""


def test_decks_report_subscribed_flag(user, make_deck):
    deck = make_deck(name="CWSP")
    decks = {d["deck_id"]: d for d in user.get("/decks").json()["decks"]}
    assert decks[deck]["subscribed"] is False
    assert user.post(f"/decks/{deck}/subscribe").status_code == 200
    decks = {d["deck_id"]: d for d in user.get("/decks").json()["decks"]}
    assert decks[deck]["subscribed"] is True


def test_subscribe_is_idempotent(user, make_deck):
    deck = make_deck()
    assert user.post(f"/decks/{deck}/subscribe").status_code == 200
    # second call must not error or duplicate
    assert user.post(f"/decks/{deck}/subscribe").status_code == 200
    assert user.get(f"/decks/{deck}").json()["deck"]["subscribed"] is True


def test_unsubscribe_removes_and_is_idempotent(user, make_deck):
    deck = make_deck()
    user.post(f"/decks/{deck}/subscribe")
    assert user.delete(f"/decks/{deck}/subscribe").status_code == 200
    assert user.get(f"/decks/{deck}").json()["deck"]["subscribed"] is False
    # unsubscribing again is a no-op, not an error
    assert user.delete(f"/decks/{deck}/subscribe").status_code == 200


def test_subscriptions_are_per_user(user, admin, make_deck):
    deck = make_deck()
    user.post(f"/decks/{deck}/subscribe")
    # admin's own view of the same public deck is unaffected
    decks = {d["deck_id"]: d for d in admin.get("/decks").json()["decks"]}
    assert decks[deck]["subscribed"] is False


def test_subscribe_unknown_deck_404(user):
    assert user.post("/decks/nope/subscribe").status_code == 404


def test_cannot_subscribe_to_others_private_deck(trusted, user):
    # trusted user's first card creates their private "My Cards" deck
    trusted.post("/cards", json={"front": "a", "back": "b"})
    deck_id = trusted.get("/cards?mine=1").json()["cards"][0]["deck_id"]
    # another user can't even see it, so can't subscribe
    assert user.post(f"/decks/{deck_id}/subscribe").status_code == 404


def test_trusted_auto_subscribed_to_my_cards(trusted):
    trusted.post("/cards", json={"front": "a", "back": "b"})
    decks = trusted.get("/decks").json()["decks"]
    mine = [d for d in decks if d["owner_id"]]
    assert len(mine) == 1
    assert mine[0]["subscribed"] is True


def test_delete_deck_cascades_subscription(admin, make_deck):
    deck = make_deck()
    admin.post(f"/decks/{deck}/subscribe")
    assert admin.delete(f"/decks/{deck}").status_code == 200
    # the deck is gone; its subscription should have cascaded away (no error)
    assert deck not in {d["deck_id"] for d in admin.get("/decks").json()["decks"]}
