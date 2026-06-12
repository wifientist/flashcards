def _propose(client, card_id, **kw):
    body = {"front": "F", "back": "B", "labels": ["x"], **kw}
    return client.post(f"/cards/{card_id}/proposals", json=body)


def test_user_can_propose_then_admin_accepts(user, admin, make_card):
    cid = make_card(front="orig", back="origback")
    r = _propose(user, cid, front="fixed front", back="fixed back", labels=["y"], note="typo")
    assert r.status_code == 200
    pid = r.json()["id"]

    # appears in the user's list as pending
    mine = user.get("/my-proposals").json()["proposals"]
    assert len(mine) == 1 and mine[0]["status"] == "pending"
    assert mine[0]["proposed"]["front"] == "fixed front"

    # admin sees it pending (with current values + proposer email)
    pend = admin.get("/proposals").json()["proposals"]
    assert any(p["id"] == pid for p in pend)
    row = next(p for p in pend if p["id"] == pid)
    assert row["current"]["front"] == "orig" and row["proposer_email"] == "user@test.com"

    # accept applies to the card
    assert admin.post(f"/proposals/{pid}/accept").status_code == 200
    assert admin.get(f"/cards/{cid}").json()["card"]["front"] == "fixed front"
    assert user.get("/my-proposals").json()["proposals"][0]["status"] == "accepted"


def test_admin_reject_does_not_change_card(user, admin, make_card):
    cid = make_card(front="orig")
    pid = _propose(user, cid, front="nope").json()["id"]
    assert admin.post(f"/proposals/{pid}/reject").status_code == 200
    assert admin.get(f"/cards/{cid}").json()["card"]["front"] == "orig"
    assert user.get("/my-proposals").json()["proposals"][0]["status"] == "rejected"


def test_reviewing_twice_is_rejected(user, admin, make_card):
    cid = make_card()
    pid = _propose(user, cid).json()["id"]
    assert admin.post(f"/proposals/{pid}/accept").status_code == 200
    assert admin.post(f"/proposals/{pid}/reject").status_code == 400


def test_proposals_admin_only(user, make_card):
    cid = make_card()
    _propose(user, cid)
    assert user.get("/proposals").status_code == 403


def test_cannot_propose_on_invisible_card(user, trusted):
    cid = trusted.post("/cards", json={"front": "secret", "back": "x"}).json()["card_id"]
    assert _propose(user, cid).status_code == 404


def test_status_filter(user, admin, make_card):
    c1, c2 = make_card(front="a"), make_card(front="b")
    p1 = _propose(user, c1).json()["id"]
    _propose(user, c2)
    admin.post(f"/proposals/{p1}/accept")
    assert [p["id"] for p in admin.get("/proposals?status=accepted").json()["proposals"]] == [p1]
    assert len(admin.get("/proposals?status=pending").json()["proposals"]) == 1
