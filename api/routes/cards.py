from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from db_models import Card, Progress, Deck
from models import CardCreate, CardUpdate, ProgressUpdate, ProgressStatus
from roles import require_roles, get_current_user, require_authenticated
import scheduler

router = APIRouter()


def _is_admin(payload) -> bool:
    return bool(payload) and "admin" in (payload.get("roles") or [])


def _visible_cards_stmt(stmt, payload):
    """Restrict a Card query to what the caller may see: public cards (owner
    NULL) plus their own private cards. Admins see everything; anonymous sees
    only public."""
    if _is_admin(payload):
        return stmt
    if payload and payload.get("authenticated"):
        return stmt.where(or_(Card.owner_id.is_(None), Card.owner_id == payload["user_id"]))
    return stmt.where(Card.owner_id.is_(None))


def _can_modify_card(card: Card, payload) -> bool:
    return _is_admin(payload) or (card.owner_id and card.owner_id == payload.get("user_id"))


def can_view_card(card: Card, payload) -> bool:
    """Public cards are visible to all; private cards only to their owner (and admins)."""
    if card.owner_id is None:
        return True
    if _is_admin(payload):
        return True
    return bool(payload) and card.owner_id == payload.get("user_id")


def _validate_public_deck(db: Session, deck_id):
    """A public (admin) card may only be filed into a public deck."""
    if not deck_id:
        return None
    deck = db.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=400, detail="Deck not found")
    if deck.owner_id is not None:
        raise HTTPException(status_code=400, detail="A public card can't go in a private deck")
    return deck_id


def _default_deck_id(db: Session, user_id: str) -> str:
    """The user's single auto 'My Cards' private deck, created on first use.
    Race-safe: a concurrent create hits the unique index and we re-read."""
    deck = db.scalar(select(Deck).where(Deck.owner_id == user_id))
    if deck:
        return deck.id
    deck = Deck(name="My Cards", owner_id=user_id, created_by=user_id)
    db.add(deck)
    try:
        db.flush()  # assign id within the current transaction
    except IntegrityError:
        db.rollback()
        deck = db.scalar(select(Deck).where(Deck.owner_id == user_id))
        return deck.id if deck else None
    return deck.id


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
        "owner_id": card.owner_id,
        "created_by": card.created_by,
        "created_at": _iso(card.created_at),
    }
    if include_progress:
        data["user_progress"] = _serialize_progress(progress)
    return data


# --- card CRUD -------------------------------------------------------------

@router.post("/cards")
def create_card(card: CardCreate, db: Session = Depends(get_db),
                payload=Depends(require_roles(["admin", "trusted"]))):
    """Create a card. Trusted users always create private (personal) cards.
    Admins create public app cards by default, or private cards with private=true."""
    is_admin = _is_admin(payload)
    # Trusted non-admins can only make private cards; admins choose.
    make_private = (not is_admin) or card.private
    user_id = payload["user_id"]
    if make_private:
        owner_id = user_id
        deck_id = _default_deck_id(db, user_id)   # auto "My Cards" deck
    else:
        owner_id = None
        deck_id = _validate_public_deck(db, card.deck_id)

    new_card = Card(
        front=card.front,
        back=card.back,
        labels=card.labels or [],
        deck_id=deck_id,
        owner_id=owner_id,
        created_by=payload["user_id"],
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return {"message": "Card created", "card_id": new_card.id, "owner_id": new_card.owner_id}


@router.get("/cards")
def get_cards(label: Optional[str] = None, deck_id: Optional[str] = None,
              deck_ids: Optional[str] = None,
              featured: bool = False, mine: bool = False,
              db: Session = Depends(get_db), payload=Depends(get_current_user)):
    """List cards the caller may see (public + their own private cards); includes
    per-card progress if authed.

    `featured=true` — only cards in featured decks (powers the public landing).
    `mine=true` — only the caller's own private cards ("My Cards").
    `deck_id` (single) or `deck_ids` (comma-separated) scope to deck(s).
    """
    stmt = select(Card)
    if label:
        stmt = stmt.where(Card.labels.any(label))
    decks = [d for d in (deck_ids.split(",") if deck_ids else []) if d] or ([deck_id] if deck_id else [])
    if decks:
        stmt = stmt.where(Card.deck_id.in_(decks))
    if featured:
        stmt = stmt.where(
            Card.deck_id.in_(select(Deck.id).where(Deck.featured.is_(True)))
        )
    if mine:
        if not (payload and payload.get("authenticated")):
            raise HTTPException(status_code=401, detail="Authentication required")
        stmt = stmt.where(Card.owner_id == payload["user_id"])
    else:
        stmt = _visible_cards_stmt(stmt, payload)
    cards = list(db.scalars(stmt.order_by(func.random())))

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
    """Get a specific card, if the caller may see it."""
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    # Hide others' private cards.
    if card.owner_id and not _is_admin(payload) and card.owner_id != (payload or {}).get("user_id"):
        raise HTTPException(status_code=404, detail="Card not found")

    authed = bool(payload and payload.get("authenticated"))
    progress = None
    if authed:
        progress = db.get(Progress, (payload["user_id"], card_id))

    return {"card": _serialize_card(card, progress, include_progress=authed)}


@router.put("/cards/{card_id}")
def update_card(card_id: str, card_update: CardUpdate, db: Session = Depends(get_db),
                payload=Depends(require_authenticated)):
    """Update card content — admins (any card) or the owner of a private card."""
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if not _can_modify_card(card, payload):
        raise HTTPException(status_code=403, detail="Not allowed")

    if card_update.front is not None:
        card.front = card_update.front
    if card_update.back is not None:
        card.back = card_update.back
    if card_update.labels is not None:
        card.labels = card_update.labels
    # Only public (admin) cards can be re-filed; private cards stay in "My Cards".
    if card.owner_id is None and "deck_id" in card_update.model_fields_set:
        card.deck_id = _validate_public_deck(db, card_update.deck_id)

    db.commit()
    return {"message": "Card updated"}


@router.delete("/cards/{card_id}")
def delete_card(card_id: str, db: Session = Depends(get_db),
                payload=Depends(require_authenticated)):
    """Delete card — admins (any) or the owner of a private card. Progress cascades."""
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if not _can_modify_card(card, payload):
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(card)
    db.commit()
    return {"message": "Card deleted"}


@router.post("/cards/{card_id}/copy")
def copy_card_to_public(card_id: str, db: Session = Depends(get_db),
                        payload=Depends(require_roles(["admin"]))):
    """Admin: copy any card into the public pool (deck-less). The original is
    untouched, so a user keeps their private card."""
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    new_card = Card(
        front=card.front,
        back=card.back,
        labels=list(card.labels or []),
        deck_id=None,
        owner_id=None,  # public
        created_by=payload["user_id"],
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return {"message": "Card copied to public", "card_id": new_card.id}


# --- user progress ---------------------------------------------------------

@router.put("/cards/{card_id}/progress")
def update_card_progress(card_id: str, progress_update: ProgressUpdate,
                         db: Session = Depends(get_db),
                         payload=Depends(require_authenticated)):
    """Update the caller's progress on a card (upsert)."""
    card = db.get(Card, card_id)
    if not card or not can_view_card(card, payload):
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
    studied = 0
    total_reviews = 0
    due_now = 0
    starred = 0
    now = scheduler.now_utc()

    rows = db.scalars(
        select(Progress).where(Progress.user_id == payload["user_id"])
    )
    for p in rows:
        studied += 1
        if p.status in status_counts:
            status_counts[p.status] += 1
        total_reviews += p.review_count or 0
        if p.flagged:
            starred += 1
        if p.due is not None and p.due <= now:
            due_now += 1

    # Total cards the caller can see (public + their own private cards).
    total_cards = db.scalar(_visible_cards_stmt(select(func.count(Card.id)), payload)) or 0
    # Untouched cards are effectively "new" — fold them in so the breakdown
    # reflects the whole library, not just cards already studied.
    status_counts["new"] += max(0, total_cards - studied)

    return {
        "total_cards": total_cards,
        "total_cards_studied": studied,
        "total_reviews": total_reviews,
        "due_now": due_now,
        "starred": starred,
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

    cards = []
    if card_ids:
        stmt = _visible_cards_stmt(select(Card).where(Card.id.in_(card_ids)), payload)
        cards = list(db.scalars(stmt))
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
