def test_new_card_appears_in_queue(user, make_card):
    make_card(front="hola")
    q = user.get("/study/queue").json()
    assert q["count"] == 1
    assert q["queue"][0]["front"] == "hola"


def test_review_advances_schedule_and_drops_from_queue(user, make_card):
    cid = make_card()
    r = user.post(f"/cards/{cid}/review", json={"rating": "good"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "learning"
    assert body["review_count"] == 1
    assert body["due"]  # next due timestamp set
    # "good" pushes due into the future, so it leaves the due queue
    assert user.get("/study/queue").json()["count"] == 0


def test_invalid_rating_400(user, make_card):
    cid = make_card()
    assert user.post(f"/cards/{cid}/review", json={"rating": "bogus"}).status_code == 400


def test_review_requires_auth(client, make_card):
    cid = make_card()
    assert client.post(f"/cards/{cid}/review", json={"rating": "good"}).status_code == 401


def test_summary_includes_totals_starred_due(user, make_card):
    cid = make_card()
    make_card()  # an untouched card -> counts as "new" in the breakdown
    user.put(f"/cards/{cid}/progress", json={"flagged": True})
    user.post(f"/cards/{cid}/review", json={"rating": "good"})
    s = user.get("/my-progress/summary").json()
    assert s["starred"] == 1
    assert s["total_reviews"] == 1
    assert s["total_cards_studied"] == 1
    assert s["total_cards"] == 2
    assert s["status_breakdown"]["new"] == 1  # the untouched card folded in
    assert "due_now" in s


def test_queue_reports_new_count(user, make_card):
    make_card()
    make_card()
    q = user.get("/study/queue").json()
    assert q["new_count"] == 2 and q["count"] == 2


def test_queue_spans_multiple_decks(user, make_card, make_deck):
    d1, d2 = make_deck(name="D1"), make_deck(name="D2")
    make_card(front="c1", deck_id=d1)
    make_card(front="c2", deck_id=d2)
    make_card(front="c3")  # no deck — excluded by the scope
    q = user.get(f"/study/queue?deck_ids={d1},{d2}").json()
    assert {c["front"] for c in q["queue"]} == {"c1", "c2"}


def test_study_decks_persist(user, make_deck):
    d = make_deck(name="X")
    assert user.get("/auth/me/study-decks").json()["deck_ids"] == []
    user.put("/auth/me/study-decks", json={"deck_ids": [d]})
    assert user.get("/auth/me/study-decks").json()["deck_ids"] == [d]


def test_flag_and_marked_list(user, make_card):
    cid = make_card()
    assert user.get("/study/marked").json()["cards"] == []

    user.put(f"/cards/{cid}/progress", json={"flagged": True})
    marked = user.get("/study/marked").json()["cards"]
    assert [c["card_id"] for c in marked] == [cid]
    assert marked[0]["user_progress"]["flagged"] is True
    assert marked[0]["user_progress"]["review_count"] == 0  # flagging != review

    user.put(f"/cards/{cid}/progress", json={"flagged": False})
    assert user.get("/study/marked").json()["cards"] == []


def test_queue_scoped_to_deck(user, make_card, make_deck):
    deck = make_deck(name="Spanish")
    make_card(front="in-deck", deck_id=deck)
    make_card(front="loose")
    q = user.get(f"/study/queue?deck_id={deck}").json()
    assert q["count"] == 1
    assert q["queue"][0]["front"] == "in-deck"
