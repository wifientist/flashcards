from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from redis_client import r1  # r1 is db1 which is the cards db for this
from models import CardCreate, CardUpdate, ProgressUpdate, ProgressStatus
import uuid
import json
from datetime import datetime
from roles import require_roles, get_current_user, require_authenticated

router = APIRouter()

def make_card_key(card_id):
    """Cards are global, not user-specific"""
    return f"card:{card_id}"

def make_label_key(label):
    """Labels are global, not user-specific"""
    return f"label:{label}"

def make_user_progress_key(user_id, card_id):
    """User-specific progress/notes for cards"""
    return f"progress:{user_id}:{card_id}"

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
        "created_by": payload["user_id"],
        "created_at": datetime.utcnow().isoformat()
    }
    
    r1.hset(card_key, mapping=card_data)
    
    # Update label indices
    for label in card.labels or []:
        r1.sadd(make_label_key(label), card_id)
    
    # Add to global card index
    r1.sadd("cards:all", card_id)
    
    return {"message": "Card created", "card_id": card_id}

@router.get("/cards")
def get_cards(request: Request, label: Optional[str] = None, payload=Depends(get_current_user)):
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
                user_id = payload["user_id"]
                progress_key = make_user_progress_key(user_id, card_id)
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
def get_card(card_id: str, request: Request, payload=Depends(get_current_user)):
    """Get a specific card - public endpoint"""
    card_key = make_card_key(card_id)
    card = r1.hgetall(card_key)
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    card["labels"] = json.loads(card.get("labels", "[]"))
    
    # Add user-specific progress if authenticated
    if payload and payload.get("authenticated"):
        user_id = payload["user_id"]
        progress_key = make_user_progress_key(user_id, card_id)
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
    
    if card_update.front is not None:
        r1.hset(card_key, "front", card_update.front)
    if card_update.back is not None:
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
def update_card_progress(card_id: str, progress_update: ProgressUpdate, payload=Depends(require_authenticated)):
    """Update user's progress on a card - authenticated users only"""
    card_key = make_card_key(card_id)
    
    if not r1.exists(card_key):
        raise HTTPException(status_code=404, detail="Card not found")
    
    user_id = payload["user_id"]
    progress_key = make_user_progress_key(user_id, card_id)
    
    updates = {}
    if progress_update.notes is not None:
        updates["notes"] = progress_update.notes
    if progress_update.status is not None:
        updates["status"] = progress_update.status.value

    # Only count this as a review when explicitly flagged by the study flow.
    # Plain note/status edits must not inflate review stats.
    if progress_update.reviewed:
        updates["last_reviewed"] = datetime.utcnow().isoformat()
        current_count = r1.hget(progress_key, "review_count") or "0"
        updates["review_count"] = str(int(current_count) + 1)

    if not updates:
        return {"message": "No changes"}

    r1.hset(progress_key, mapping=updates)

    return {"message": "Progress updated"}

@router.get("/my-progress")
def get_my_progress(payload=Depends(require_authenticated)):
    """Get user's progress across all cards"""
    user_id = payload["user_id"]
    
    # Find all progress entries for this user
    cursor = 0
    pattern = f"progress:{user_id}:*"
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

@router.get("/my-progress/summary")
def get_my_progress_summary(payload=Depends(require_authenticated)):
    """Get summary of user's progress statistics"""
    user_id = payload["user_id"]
    
    # Find all progress entries for this user
    cursor = 0
    pattern = f"progress:{user_id}:*"
    
    status_counts = {
        "new": 0,
        "learning": 0,
        "review": 0,
        "mastered": 0,
        "difficult": 0
    }
    
    total_cards = 0
    total_reviews = 0
    
    while True:
        cursor, keys = r1.scan(cursor=cursor, match=pattern, count=100)
        for key in keys:
            progress = r1.hgetall(key)
            if progress:
                total_cards += 1
                status = progress.get("status", "new")
                if status in status_counts:
                    status_counts[status] += 1
                
                review_count = int(progress.get("review_count", 0))
                total_reviews += review_count
        
        if cursor == 0:
            break
    
    return {
        "total_cards_studied": total_cards,
        "total_reviews": total_reviews,
        "status_breakdown": status_counts
    }

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

@router.get("/cards/by-status/{status}")
def get_cards_by_status(status: str, payload=Depends(require_authenticated)):
    """Get cards filtered by user's progress status"""
    user_id = payload["user_id"]
    
    # Validate status
    try:
        ProgressStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    # Find all progress entries for this user with the specified status
    cursor = 0
    pattern = f"progress:{user_id}:*"
    matching_card_ids = []
    
    while True:
        cursor, keys = r1.scan(cursor=cursor, match=pattern, count=100)
        for key in keys:
            progress = r1.hgetall(key)
            if progress and progress.get("status") == status:
                card_id = key.split(":")[-1]
                matching_card_ids.append(card_id)
        
        if cursor == 0:
            break
    
    # If looking for "new" status, also include cards with no progress
    if status == "new":
        all_cards = r1.smembers("cards:all")
        for card_id in all_cards:
            progress_key = make_user_progress_key(user_id, card_id)
            if not r1.exists(progress_key):
                matching_card_ids.append(card_id)
    
    # Get card details
    cards = []
    for card_id in matching_card_ids:
        card_key = make_card_key(card_id)
        card = r1.hgetall(card_key)
        if card:
            card["labels"] = json.loads(card.get("labels", "[]"))
            
            # Add user progress
            progress_key = make_user_progress_key(user_id, card_id)
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
    
    return {"cards": cards, "status": status, "count": len(cards)}

@router.delete("/my-progress/{card_id}")
def reset_card_progress(card_id: str, payload=Depends(require_authenticated)):
    """Reset user's progress for a specific card"""
    user_id = payload["user_id"]
    progress_key = make_user_progress_key(user_id, card_id)
    
    if not r1.exists(progress_key):
        raise HTTPException(status_code=404, detail="No progress found for this card")
    
    r1.delete(progress_key)
    return {"message": "Progress reset for card"}

@router.delete("/my-progress")
def reset_all_progress(payload=Depends(require_authenticated)):
    """Reset all progress for the current user"""
    user_id = payload["user_id"]
    
    # Find all progress entries for this user
    cursor = 0
    pattern = f"progress:{user_id}:*"
    deleted_count = 0
    
    while True:
        cursor, keys = r1.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            r1.delete(*keys)
            deleted_count += len(keys)
        if cursor == 0:
            break
    
    return {"message": f"Reset progress for {deleted_count} cards"}