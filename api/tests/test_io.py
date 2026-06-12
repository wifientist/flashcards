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
    assert r.json() == {"imported": 2, "skipped": 1}
    assert admin.get(f"/cards?deck_id={deck}").json()["cards"].__len__() == 2


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
