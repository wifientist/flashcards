import json

JSON_PAYLOAD = json.dumps({"cards": [
    {"front": "bonjour", "back": "hello", "labels": ["greeting", "a1"]},
    {"front": "merci", "back": "thanks", "labels": ["a1"]},
    {"front": "", "back": "no front"},  # incomplete -> skipped
]})


def test_non_admin_cannot_import(user):
    assert user.post("/import/cards", json={"format": "json", "content": "{}"}).status_code == 403


def test_import_json_counts(admin, make_deck):
    deck = make_deck()
    r = admin.post("/import/cards", json={"format": "json", "content": JSON_PAYLOAD, "deck_id": deck})
    assert r.status_code == 200
    assert r.json() == {"imported": 2, "skipped": 1, "updated": 0}
    assert admin.get(f"/cards?deck_id={deck}").json()["cards"].__len__() == 2


def test_import_dedups_against_existing_and_within_batch(admin, make_deck):
    deck = make_deck()
    admin.post("/import/cards", json={"format": "json", "content": JSON_PAYLOAD, "deck_id": deck})
    # Re-import an overlapping list (bonjour dup, BONJOUR case-dup, one new).
    payload = json.dumps({"cards": [
        {"front": "bonjour", "back": "hello"},   # exact dup of existing
        {"front": "BONJOUR", "back": "Hello"},   # case-insensitive dup
        {"front": "au revoir", "back": "goodbye"},  # new
    ]})
    r = admin.post("/import/cards", json={"format": "json", "content": payload, "deck_id": deck})
    assert r.json() == {"imported": 1, "skipped": 2, "updated": 0}
    assert len(admin.get(f"/cards?deck_id={deck}").json()["cards"]) == 3


def test_import_update_existing_refreshes_labels(admin, make_deck):
    deck = make_deck()
    # First import: cards land without the chapter labels.
    admin.post("/import/cards", json={"format": "json", "content": json.dumps({"cards": [
        {"front": "bonjour", "back": "hello"},
        {"front": "merci", "back": "thanks"},
    ]}), "deck_id": deck})
    # Re-upload the same fronts/backs, now WITH labels, in update mode.
    payload = json.dumps({"cards": [
        {"front": "bonjour", "back": "hello", "labels": ["CH1"]},
        {"front": "merci", "back": "thanks", "labels": ["CH1"]},
        {"front": "au revoir", "back": "goodbye", "labels": ["CH2"]},  # genuinely new
    ]})
    r = admin.post("/import/cards", json={
        "format": "json", "content": payload, "deck_id": deck, "update_existing": True,
    })
    assert r.json() == {"imported": 1, "updated": 2, "skipped": 0}
    cards = {c["front"]: c for c in admin.get(f"/cards?deck_id={deck}").json()["cards"]}
    assert cards["bonjour"]["labels"] == ["CH1"]
    assert cards["au revoir"]["labels"] == ["CH2"]


def test_import_update_existing_noop_when_labels_match(admin, make_deck):
    deck = make_deck()
    admin.post("/import/cards", json={"format": "json", "content": JSON_PAYLOAD, "deck_id": deck})
    # Same labels again in update mode → nothing changes, all skipped.
    r = admin.post("/import/cards", json={
        "format": "json", "content": JSON_PAYLOAD, "deck_id": deck, "update_existing": True,
    })
    assert r.json() == {"imported": 0, "updated": 0, "skipped": 3}


def test_import_dedup_is_per_deck(admin, make_deck):
    a, b = make_deck(), make_deck()
    admin.post("/import/cards", json={"format": "json", "content": JSON_PAYLOAD, "deck_id": a})
    # Same cards into a different deck are NOT treated as duplicates.
    r = admin.post("/import/cards", json={"format": "json", "content": JSON_PAYLOAD, "deck_id": b})
    assert r.json() == {"imported": 2, "skipped": 1, "updated": 0}


def test_import_into_private_deck_rejected(admin, trusted):
    trusted.post("/cards", json={"front": "x", "back": "y"})  # creates trusted's My Cards deck
    priv = next(d["deck_id"] for d in trusted.get("/decks").json()["decks"] if d["owner_id"])
    r = admin.post("/import/cards", json={"format": "json", "content": "{}", "deck_id": priv})
    assert r.status_code == 400


def test_bad_format_400(admin):
    assert admin.post("/import/cards", json={"format": "xml", "content": "x"}).status_code == 400


def test_malformed_json_400(admin):
    assert admin.post("/import/cards", json={"format": "json", "content": "{not json"}).status_code == 400


def test_export_csv_roundtrip(admin, make_deck):
    src = make_deck(name="src")
    admin.post("/import/cards", json={"format": "json", "content": JSON_PAYLOAD, "deck_id": src})

    csv_text = admin.get(f"/export/cards?format=csv&deck_id={src}").text
    assert "front,back,labels" in csv_text
    assert "greeting|a1" in csv_text  # labels joined with |

    dst = make_deck(name="dst")
    r = admin.post("/import/cards", json={"format": "csv", "content": csv_text, "deck_id": dst})
    assert r.json()["imported"] == 2
    # labels parsed back into a list
    cards = {c["front"]: c for c in admin.get(f"/cards?deck_id={dst}").json()["cards"]}
    assert cards["bonjour"]["labels"] == ["greeting", "a1"]


def test_export_requires_auth(client):
    assert client.get("/export/cards").status_code == 401


def test_import_sanitizes_garbage_chars(admin):
    # NUL control char + Unicode replacement char should become spaces; a real
    # em-dash must be preserved.
    content = json.dumps({"cards": [{"front": "a\x00b�c", "back": "x — y"}]})
    r = admin.post("/import/cards", json={"format": "json", "content": content})
    assert r.json()["imported"] == 1
    card = admin.get("/cards").json()["cards"][0]
    assert card["front"] == "a b c"   # control + replacement -> spaces
    assert card["back"] == "x — y"    # em-dash preserved
