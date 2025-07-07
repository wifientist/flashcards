from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from redis_client import r1  # r1 is db1 which is the cards db for this
from models import CardCreate
import uuid
import json
from roles import require_roles, require_authenticated

router = APIRouter()

def make_card_key(user_id, card_id):
    return f"card:{user_id}:{card_id}"

def make_label_key(user_id, label):
    return f"label:{user_id}:{label}"

@router.post("/cards")
def create_card(card: CardCreate, payload=Depends(require_roles(["admin", "editor"]))):
    user_id = payload["session_id"]  # Using session_id as user identifier for now

    card_id = str(uuid.uuid4())
    card_key = make_card_key(user_id, card_id)

    card_data = {
        "card_id": card_id,
        "front": card.front,
        "back": card.back,
        "labels": json.dumps(card.labels or [])
    }

    r1.hset(card_key, mapping=card_data)

    # Update label indices
    for label in card.labels or []:
        r1.sadd(make_label_key(user_id, label), card_id)

    return {"message": "Card created", "card_id": card_id}

@router.get("/cards")
def get_cards(request: Request, label: Optional[str] = None, payload=Depends(require_authenticated)):
    user_id = payload["session_id"]

    card_keys = []

    if label:
        card_ids = r1.smembers(make_label_key(user_id, label))
        card_keys = [make_card_key(user_id, card_id) for card_id in card_ids]
    else:
        # Scan all cards for user
        cursor = 0
        pattern = f"card:*" #{user_id}:*" #dont want to filter by userid anymore 
        while True:
            cursor, keys = r1.scan(cursor=cursor, match=pattern, count=100)  #TODO remove count limit probably
            card_keys.extend(keys)
            if cursor == 0:
                break

    cards = []
    for key in card_keys:
        card = r1.hgetall(key)
        if card:
            card["labels"] = json.loads(card.get("labels", "[]"))
            cards.append(card)

    return {"cards": cards}

@router.put("/cards/{card_id}")
def update_card(card_id: str, front: Optional[str] = None, back: Optional[str] = None, labels: Optional[List[str]] = None, payload=Depends(require_roles(["admin", "editor"]))):
    user_id = payload["session_id"]
    card_key = make_card_key(user_id, card_id)

    if not r1.exists(card_key):
        raise HTTPException(status_code=404, detail="Card not found")

    if front:
        r1.hset(card_key, "front", front)
    if back:
        r1.hset(card_key, "back", back)
    if labels is not None:
        # Remove old labels
        old_labels = json.loads(r1.hget(card_key, "labels") or "[]")
        for label in old_labels:
            r1.srem(make_label_key(user_id, label), card_id)

        # Add new labels
        for label in labels:
            r1.sadd(make_label_key(user_id, label), card_id)

        r1.hset(card_key, "labels", json.dumps(labels))

    return {"message": "Card updated"}

@router.delete("/cards/{card_id}")
def delete_card(card_id: str, payload=Depends(require_roles(["admin", "editor"]))):
    user_id = payload["session_id"]
    card_key = make_card_key(user_id, card_id)

    if not r1.exists(card_key):
        raise HTTPException(status_code=404, detail="Card not found")

    # Clean up label indices
    labels = json.loads(r1.hget(card_key, "labels") or "[]")
    for label in labels:
        r1.srem(make_label_key(user_id, label), card_id)

    r1.delete(card_key)

    return {"message": "Card deleted"}
