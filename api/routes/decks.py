from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from database import get_db
from db_models import Deck, Card, DeckSubscription
from models import DeckCreate, DeckUpdate
from roles import require_roles, get_current_user, require_authenticated
from routes.cards import _is_admin, _default_deck_id

router = APIRouter()


def _serialize_deck(deck: Deck, card_count: int = 0, subscribed: bool = False) -> dict:
    return {
        "deck_id": deck.id,
        "name": deck.name,
        "description": deck.description,
        "featured": deck.featured,
        "owner_id": deck.owner_id,
        "created_by": deck.created_by,
        "created_at": deck.created_at.isoformat() if deck.created_at else None,
        "card_count": card_count,
        "subscribed": subscribed,
    }


def _can_view_deck(deck: Deck, payload) -> bool:
    """Public decks are visible to all; private decks only to their owner (and admins)."""
    if deck.owner_id is None:
        return True
    return _is_admin(payload) or deck.owner_id == (payload or {}).get("user_id")


def _visible_decks_stmt(stmt, payload):
    """Public decks (owner NULL) + the caller's own private deck. Even admins
    only see their own private deck in the list — other users' "My Cards" decks
    aren't theirs to manage here (per-user oversight lives on the Cards page)."""
    if payload and payload.get("authenticated"):
        return stmt.where(or_(Deck.owner_id.is_(None), Deck.owner_id == payload["user_id"]))
    return stmt.where(Deck.owner_id.is_(None))


@router.get("/decks")
def list_decks(db: Session = Depends(get_db), payload=Depends(get_current_user)):
    """Decks the caller may see (public + their own), with card counts."""
    # Ensure card-creators always have their "My Cards" deck (shown even at 0 cards).
    if payload and payload.get("authenticated") and (
        set(payload.get("roles", [])) & {"trusted", "admin"}
    ):
        _default_deck_id(db, payload["user_id"])
        db.commit()

    counts = dict(
        db.execute(
            select(Card.deck_id, func.count())
            .where(Card.deck_id.is_not(None))
            .group_by(Card.deck_id)
        ).all()
    )
    # Batch-load the caller's subscriptions so each deck can report `subscribed`.
    subscribed = set()
    if payload and payload.get("authenticated"):
        subscribed = set(db.scalars(
            select(DeckSubscription.deck_id)
            .where(DeckSubscription.user_id == payload["user_id"])
        ))
    decks = db.scalars(_visible_decks_stmt(select(Deck), payload).order_by(Deck.name))
    return {"decks": [
        _serialize_deck(d, counts.get(d.id, 0), d.id in subscribed) for d in decks
    ]}


@router.get("/decks/{deck_id}")
def get_deck(deck_id: str, db: Session = Depends(get_db), payload=Depends(get_current_user)):
    deck = db.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    # Hide others' private decks.
    if not _can_view_deck(deck, payload):
        raise HTTPException(status_code=404, detail="Deck not found")
    count = db.scalar(select(func.count()).where(Card.deck_id == deck_id)) or 0
    subscribed = False
    if payload and payload.get("authenticated"):
        subscribed = db.get(DeckSubscription, (payload["user_id"], deck_id)) is not None
    return {"deck": _serialize_deck(deck, count, subscribed)}


@router.post("/decks")
def create_deck(deck: DeckCreate, db: Session = Depends(get_db),
                payload=Depends(require_roles(["admin"]))):
    """Create a public deck — admin only. Users' private cards live in an
    auto-created 'My Cards' deck instead (see routes/cards.py)."""
    new_deck = Deck(
        name=deck.name,
        description=deck.description,
        featured=deck.featured,
        owner_id=None,  # admin decks are public
        created_by=payload["user_id"],
    )
    db.add(new_deck)
    db.commit()
    db.refresh(new_deck)
    return {"message": "Deck created", "deck_id": new_deck.id}


@router.put("/decks/{deck_id}")
def update_deck(deck_id: str, deck_update: DeckUpdate, db: Session = Depends(get_db),
                payload=Depends(require_roles(["admin"]))):
    """Update a deck - admin only."""
    deck = db.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck_update.name is not None:
        deck.name = deck_update.name
    if deck_update.description is not None:
        deck.description = deck_update.description
    if deck_update.featured is not None:
        deck.featured = deck_update.featured
    db.commit()
    return {"message": "Deck updated"}


@router.delete("/decks/{deck_id}")
def delete_deck(deck_id: str, delete_cards: bool = False,
                db: Session = Depends(get_db),
                payload=Depends(require_roles(["admin"]))):
    """Delete a deck - admin only.

    By default the deck's cards are kept (deck_id -> NULL, unfiled). With
    delete_cards=true the cards in the deck are permanently deleted first (and
    every user's progress on them cascades away) — for wiping a deck to re-import
    it cleanly. Cards must be removed before the deck, since deleting the deck
    would otherwise null their deck_id and orphan them."""
    deck = db.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    deleted_cards = 0
    if delete_cards:
        deleted_cards = db.query(Card).filter(Card.deck_id == deck_id).delete(
            synchronize_session=False
        )
    db.delete(deck)
    db.commit()
    return {"message": "Deck deleted", "deleted_cards": deleted_cards}


@router.post("/decks/{deck_id}/subscribe")
def subscribe_deck(deck_id: str, db: Session = Depends(get_db),
                   payload=Depends(require_authenticated)):
    """Subscribe the caller to a deck. Idempotent. Subscriptions are the study
    universe — the queue and card list scope to subscribed decks."""
    deck = db.get(Deck, deck_id)
    if not deck or not _can_view_deck(deck, payload):
        raise HTTPException(status_code=404, detail="Deck not found")
    user_id = payload["user_id"]
    if not db.get(DeckSubscription, (user_id, deck_id)):
        db.add(DeckSubscription(user_id=user_id, deck_id=deck_id))
        db.commit()
    return {"message": "Subscribed", "deck_id": deck_id, "subscribed": True}


@router.delete("/decks/{deck_id}/subscribe")
def unsubscribe_deck(deck_id: str, db: Session = Depends(get_db),
                     payload=Depends(require_authenticated)):
    """Unsubscribe the caller from a deck. Idempotent."""
    sub = db.get(DeckSubscription, (payload["user_id"], deck_id))
    if sub:
        db.delete(sub)
        db.commit()
    return {"message": "Unsubscribed", "deck_id": deck_id, "subscribed": False}
