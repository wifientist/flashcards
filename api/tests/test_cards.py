def test_user_cannot_create_card(user):
    assert user.post("/cards", json={"front": "a", "back": "b"}).status_code == 403


def test_anonymous_cannot_create_card(client):
    assert client.post("/cards", json={"front": "a", "back": "b"}).status_code == 401


def test_create_and_list_card(admin, make_card):
    cid = make_card(front="2+2", back="4", labels=["math"])
    cards = admin.get("/cards").json()["cards"]
    assert any(c["card_id"] == cid and c["front"] == "2+2" for c in cards)


def test_get_cards_includes_progress_when_authed(user, make_card):
    make_card()
    card = user.get("/cards").json()["cards"][0]
    assert card["user_progress"]["status"] == "new"


def test_anonymous_list_has_no_progress(client, make_card):
    make_card()
    card = client.get("/cards").json()["cards"][0]
    assert "user_progress" not in card


def test_update_card(admin, make_card):
    cid = make_card(front="old")
    assert admin.put(f"/cards/{cid}", json={"front": "new"}).status_code == 200
    assert admin.get(f"/cards/{cid}").json()["card"]["front"] == "new"


def test_delete_card_cascades_progress(admin, user, make_card):
    cid = make_card()
    user.put(f"/cards/{cid}/progress", json={"notes": "hi"})
    assert admin.delete(f"/cards/{cid}").status_code == 200
    assert admin.get(f"/cards/{cid}").status_code == 404
    # progress for the deleted card is gone
    assert user.get("/my-progress").json()["progress"] == []


def test_labels_aggregation(admin, make_card):
    make_card(labels=["a", "b"])
    make_card(labels=["a"])
    labels = {l["label"]: l["card_count"] for l in admin.get("/labels").json()["labels"]}
    assert labels == {"a": 2, "b": 1}


def test_note_edit_does_not_count_as_review(user, make_card):
    cid = make_card()
    user.put(f"/cards/{cid}/progress", json={"notes": "studying", "status": "learning"})
    prog = user.get("/cards").json()["cards"][0]["user_progress"]
    assert prog["review_count"] == 0
    assert prog["notes"] == "studying"
