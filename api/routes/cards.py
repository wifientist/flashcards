from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database import get_db
from db_models import Card, Progress, Deck
from models import CardCreate, CardUpdate, ProgressUpdate, ProgressStatus
from roles import require_roles, get_current_user, require_authenticated

router = APIRouter()


# --- serialization helpers -------------------------------------------------

def _iso(dt):
    return dt.isoformat() if dt else None


def _serialize_progress(p: Optional[Progress]) -> dict:
    if not p:
        return {"notes": "", "status": "new", "last_reviewed": None,
                "review_count": 0, "due": None, "flagged": False}
    return {
        "notes": p.notes or "",
        "status": p.status or "new",
        "last_reviewed": _iso(p.last_reviewed),
        "review_count": p.review_count or 0,
        "due": _iso(p.due),
        "flagged": bool(p.flagged),
    }


def _serialize_card(card: Card, progress: Optional[Progress] = None,
                    include_progress: bool = False) -> dict:
    data = {
        "card_id": card.id,
        "front": card.front,
        "back": card.back,
        "labels": list(card.labels or []),
        "deck_id": card.deck_id,
        "created_by": card.created_by,
        "created_at": _iso(card.created_at),
    }
    if include_progress:
        data["user_progress"] = _serialize_progress(progress)
    return data


# --- card CRUD -------------------------------------------------------------

@router.post("/cards")
def create_card(card: CardCreate, db: Session = Depends(get_db),
                payload=Depends(require_roles(["admin"]))):
    """Only admins can create cards"""
    if card.deck_id and not db.get(Deck, card.deck_id):
        raise HTTPException(status_code=400, detail="Deck not found")
    new_card = Card(
        front=card.front,
        back=card.back,
        labels=card.labels or [],
        deck_id=card.deck_id,
        created_by=payload["user_id"],
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return {"message": "Card created", "card_id": new_card.id}


@router.get("/cards")
def get_cards(label: Optional[str] = None, deck_id: Optional[str] = None,
              featured: bool = False,
              db: Session = Depends(get_db), payload=Depends(get_current_user)):
    """List cards (public); includes the caller's per-card progress if authed.

    `featured=true` returns only cards in featured decks — this powers the
    public, unauthenticated landing.
    """
    stmt = select(Card)
    if label:
        stmt = stmt.where(Card.labels.any(label))
    if deck_id:
        stmt = stmt.where(Card.deck_id == deck_id)
    if featured:
        stmt = stmt.where(
            Card.deck_id.in_(select(Deck.id).where(Deck.featured.is_(True)))
        )
    cards = list(db.scalars(stmt))

    authed = bool(payload and payload.get("authenticated"))
    progress_by_card = {}
    if authed:
        rows = db.scalars(
            select(Progress).where(Progress.user_id == payload["user_id"])
        )
        progress_by_card = {p.card_id: p for p in rows}

    return {
        "cards": [
            _serialize_card(c, progress_by_card.get(c.id), include_progress=authed)
            for c in cards
        ]
    }


@router.get("/cards/{card_id}")
def get_card(card_id: str, db: Session = Depends(get_db),
             payload=Depends(get_current_user)):
    """Get a specific card (public)."""
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    authed = bool(payload and payload.get("authenticated"))
    progress = None
    if authed:
        progress = db.get(Progress, (payload["user_id"], card_id))

    return {"card": _serialize_card(card, progress, include_progress=authed)}


@router.put("/cards/{card_id}")
def update_card(card_id: str, card_update: CardUpdate, db: Session = Depends(get_db),
                payload=Depends(require_roles(["admin"]))):
    """Update card content - admin only"""
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if card_update.front is not None:
        card.front = card_update.front
    if card_update.back is not None:
        card.back = card_update.back
    if card_update.labels is not None:
        card.labels = card_update.labels
    # deck_id is nullable, so distinguish "omitted" from "explicitly set to null".
    if "deck_id" in card_update.model_fields_set:
        if card_update.deck_id and not db.get(Deck, card_update.deck_id):
            raise HTTPException(status_code=400, detail="Deck not found")
        card.deck_id = card_update.deck_id

    db.commit()
    return {"message": "Card updated"}


@router.delete("/cards/{card_id}")
def delete_card(card_id: str, db: Session = Depends(get_db),
                payload=Depends(require_roles(["admin"]))):
    """Delete card - admin only. Progress rows cascade-delete."""
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()
    return {"message": "Card deleted"}


# --- user progress ---------------------------------------------------------

@router.put("/cards/{card_id}/progress")
def update_card_progress(card_id: str, progress_update: ProgressUpdate,
                         db: Session = Depends(get_db),
                         payload=Depends(require_authenticated)):
    """Update the caller's progress on a card (upsert)."""
    if not db.get(Card, card_id):
        raise HTTPException(status_code=404, detail="Card not found")

    user_id = payload["user_id"]
    progress = db.get(Progress, (user_id, card_id))
    if not progress:
        progress = Progress(user_id=user_id, card_id=card_id)
        db.add(progress)

    if progress_update.notes is not None:
        progress.notes = progress_update.notes
    if progress_update.status is not None:
        progress.status = progress_update.status.value
    if progress_update.flagged is not None:
        progress.flagged = progress_update.flagged

    # Only an explicit review event updates review stats.
    if progress_update.reviewed:
        progress.last_reviewed = datetime.utcnow()
        progress.review_count = (progress.review_count or 0) + 1

    db.commit()
    return {"message": "Progress updated"}


@router.get("/my-progress")
def get_my_progress(db: Session = Depends(get_db),
                    payload=Depends(require_authenticated)):
    """Get the caller's progress across all cards."""
    rows = db.scalars(
        select(Progress).where(Progress.user_id == payload["user_id"])
    )
    return {
        "progress": [
            {"card_id": p.card_id, **_serialize_progress(p)} for p in rows
        ]
    }


@router.get("/my-progress/summary")
def get_my_progress_summary(db: Session = Depends(get_db),
                            payload=Depends(require_authenticated)):
    """Summary statistics of the caller's progress."""
    status_counts = {s.value: 0 for s in ProgressStatus}
    total_cards = 0
    total_reviews = 0

    rows = db.scalars(
        select(Progress).where(Progress.user_id == payload["user_id"])
    )
    for p in rows:
        total_cards += 1
        if p.status in status_counts:
            status_counts[p.status] += 1
        total_reviews += p.review_count or 0

    return {
        "total_cards_studied": total_cards,
        "total_reviews": total_reviews,
        "status_breakdown": status_counts,
    }


@router.get("/labels")
def get_labels(db: Session = Depends(get_db)):
    """All labels with their card counts (public)."""
    sub = select(func.unnest(Card.labels).label("label")).subquery()
    rows = db.execute(
        select(sub.c.label, func.count()).group_by(sub.c.label)
    ).all()
    return {"labels": [{"label": label, "card_count": count} for label, count in rows]}


@router.get("/cards/by-status/{status}")
def get_cards_by_status(status: str, db: Session = Depends(get_db),
                        payload=Depends(require_authenticated)):
    """Cards filtered by the caller's progress status."""
    try:
        ProgressStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")

    user_id = payload["user_id"]
    progress_rows = db.scalars(
        select(Progress).where(
            Progress.user_id == user_id, Progress.status == status
        )
    )
    progress_by_card = {p.card_id: p for p in progress_rows}
    card_ids = set(progress_by_card.keys())

    # "new" also includes cards the user has never touched.
    if status == "new":
        tracked = db.scalars(
            select(Progress.card_id).where(Progress.user_id == user_id)
        )
        tracked_ids = set(tracked)
        all_ids = set(db.scalars(select(Card.id)))
        card_ids |= (all_ids - tracked_ids)

    cards = list(db.scalars(select(Card).where(Card.id.in_(card_ids)))) if card_ids else []
    serialized = [
        _serialize_card(c, progress_by_card.get(c.id), include_progress=True)
        for c in cards
    ]
    return {"cards": serialized, "status": status, "count": len(serialized)}


@router.delete("/my-progress/{card_id}")
def reset_card_progress(card_id: str, db: Session = Depends(get_db),
                        payload=Depends(require_authenticated)):
    """Reset the caller's progress for a specific card."""
    progress = db.get(Progress, (payload["user_id"], card_id))
    if not progress:
        raise HTTPException(status_code=404, detail="No progress found for this card")
    db.delete(progress)
    db.commit()
    return {"message": "Progress reset for card"}


@router.delete("/my-progress")
def reset_all_progress(db: Session = Depends(get_db),
                       payload=Depends(require_authenticated)):
    """Reset all progress for the caller."""
    deleted = db.query(Progress).filter(
        Progress.user_id == payload["user_id"]
    ).delete(synchronize_session=False)
    db.commit()
    return {"message": f"Reset progress for {deleted} cards"}
