from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from redis_client import r1  # r1 is db1 which is the cards db for this
from models import CardCreate, CardUpdate, ProgressUpdate, ProgressStatus
import uuid
import json
from roles import require_roles, get_current_session

router = APIRouter()

def make_card_key(card_id):
    """Cards are global, not user-specific"""
    return f"card:{card_id}"

def make_label_key(label):
    """Labels are global, not user-specific"""
    return f"label:{label}"

def make_user_progress_key(session_id, card_id):
    """User-specific progress/notes for cards"""
    return f"progress:{session_id}:{card_id}"

@router.post("/cards")
def create_card(card: CardCreate, payload=Depends(require_roles(["admin"]))):
    """Only admins can create cards"""
    card_id = str(uuid.uuid4())
    card_key = make_card_key(card_id)
    
    card_data = {
        "card_id": card_id,
        "front": card.front,
        "back": card.back,
        "labels": json.dumps(card.labels or []),
        "created_by": payload["session_id"],
        "created_at": json.dumps({"timestamp": "now"})  # You might want to use actual timestamp
    }
    
    r1.hset(card_key, mapping=card_data)
    
    # Update label indices
    for label in card.labels or []:
        r1.sadd(make_label_key(label), card_id)
    
    # Add to global card index
    r1.sadd("cards:all", card_id)
    
    return {"message": "Card created", "card_id": card_id}

@router.get("/cards")
def get_cards(request: Request, label: Optional[str] = None, payload=Depends(get_current_session)):
    """Get cards - public endpoint, but shows different data based on auth"""
    
    card_ids = set()
    
    if label:
        # Get cards by label
        card_ids = r1.smembers(make_label_key(label))
    else:
        # Get all cards
        card_ids = r1.smembers("cards:all")
    
    cards = []
    for card_id in card_ids:
        card_key = make_card_key(card_id)
        card = r1.hgetall(card_key)
        if card:
            card["labels"] = json.loads(card.get("labels", "[]"))
            
            # Add user-specific progress if authenticated
            if payload and payload.get("authenticated"):
                session_id = payload["session_id"]
                progress_key = make_user_progress_key(session_id, card_id)
                progress = r1.hgetall(progress_key)
                if progress:
                    card["user_progress"] = {
                        "notes": progress.get("notes", ""),
                        "status": progress.get("status", "new"),
                        "last_reviewed": progress.get("last_reviewed"),
                        "review_count": int(progress.get("review_count", 0))
                    }
                else:
                    card["user_progress"] = {
                        "notes": "",
                        "status": "new",
                        "last_reviewed": None,
                        "review_count": 0
                    }
            
            cards.append(card)
    
    return {"cards": cards}

@router.get("/cards/{card_id}")
def get_card(card_id: str, request: Request, payload=Depends(get_current_session)):
    """Get a specific card - public endpoint"""
    card_key = make_card_key(card_id)
    card = r1.hgetall(card_key)
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    card["labels"] = json.loads(card.get("labels", "[]"))
    
    # Add user-specific progress if authenticated
    if payload and payload.get("authenticated"):
        session_id = payload["session_id"]
        progress_key = make_user_progress_key(session_id, card_id)
        progress = r1.hgetall(progress_key)
        if progress:
            card["user_progress"] = {
                "notes": progress.get("notes", ""),
                "status": progress.get("status", "new"),
                "last_reviewed": progress.get("last_reviewed"),
                "review_count": int(progress.get("review_count", 0))
            }
    
    return {"card": card}

@router.put("/cards/{card_id}")
def update_card(card_id: str, card_update: CardUpdate, payload=Depends(require_roles(["admin"]))):
    """Update card content - admin only"""
    card_key = make_card_key(card_id)
    
    if not r1.exists(card_key):
        raise HTTPException(status_code=404, detail="Card not found")
    
    if card_update.front:
        r1.hset(card_key, "front", card_update.front)
    if card_update.back:
        r1.hset(card_key, "back", card_update.back)
    if card_update.labels is not None:
        # Remove old labels
        old_labels = json.loads(r1.hget(card_key, "labels") or "[]")
        for label in old_labels:
            r1.srem(make_label_key(label), card_id)
        
        # Add new labels
        for label in card_update.labels:
            r1.sadd(make_label_key(label), card_id)
        
        r1.hset(card_key, "labels", json.dumps(card_update.labels))
    
    return {"message": "Card updated"}

@router.delete("/cards/{card_id}")
def delete_card(card_id: str, payload=Depends(require_roles(["admin"]))):
    """Delete card - admin only"""
    card_key = make_card_key(card_id)
    
    if not r1.exists(card_key):
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Clean up label indices
    labels = json.loads(r1.hget(card_key, "labels") or "[]")
    for label in labels:
        r1.srem(make_label_key(label), card_id)
    
    # Remove from global index
    r1.srem("cards:all", card_id)
    
    # Clean up all user progress for this card
    # Note: This is expensive - you might want to do this in background
    cursor = 0
    pattern = f"progress:*:{card_id}"
    while True:
        cursor, keys = r1.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            r1.delete(*keys)
        if cursor == 0:
            break
    
    r1.delete(card_key)
    
    return {"message": "Card deleted"}

# User progress endpoints
@router.put("/cards/{card_id}/progress")
def update_card_progress(card_id: str, progress_update: ProgressUpdate, payload=Depends(require_roles(["user", "admin"]))):
    """Update user's progress on a card - authenticated users only"""
    card_key = make_card_key(card_id)
    
    if not r1.exists(card_key):
        raise HTTPException(status_code=404, detail="Card not found")
    
    session_id = payload["session_id"]
    progress_key = make_user_progress_key(session_id, card_id)
    
    updates = {}
    if progress_update.notes is not None:
        updates["notes"] = progress_update.notes
    if progress_update.status is not None:
        updates["status"] = progress_update.status.value
    
    # Always update last_reviewed and increment review_count
    updates["last_reviewed"] = json.dumps({"timestamp": "now"})  # Use actual timestamp
    
    # Get current review count and increment
    current_count = r1.hget(progress_key, "review_count") or "0"
    updates["review_count"] = str(int(current_count) + 1)
    
    r1.hset(progress_key, mapping=updates)
    
    return {"message": "Progress updated"}

@router.get("/my-progress")
def get_my_progress(payload=Depends(require_roles(["user", "admin"]))):
    """Get user's progress across all cards"""
    session_id = payload["session_id"]
    
    # Find all progress entries for this user
    cursor = 0
    pattern = f"progress:{session_id}:*"
    progress_entries = []
    
    while True:
        cursor, keys = r1.scan(cursor=cursor, match=pattern, count=100)
        for key in keys:
            progress = r1.hgetall(key)
            if progress:
                card_id = key.split(":")[-1]  # Extract card_id from key
                progress["card_id"] = card_id
                progress_entries.append(progress)
        if cursor == 0:
            break
    
    return {"progress": progress_entries}

@router.get("/labels")
def get_labels():
    """Get all available labels - public endpoint"""
    cursor = 0
    pattern = "label:*"
    labels = []
    
    while True:
        cursor, keys = r1.scan(cursor=cursor, match=pattern, count=100)
        for key in keys:
            label = key.split(":", 1)[1]  # Extract label from key
            card_count = r1.scard(key)
            labels.append({"label": label, "card_count": card_count})
        if cursor == 0:
            break
    
    return {"labels": labels}