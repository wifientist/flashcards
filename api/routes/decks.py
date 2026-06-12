from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from database import get_db
from db_models import Deck, Card
from models import DeckCreate, DeckUpdate
from roles import require_roles, require_authenticated, get_current_user
from routes.cards import _is_admin

router = APIRouter()


def _serialize_deck(deck: Deck, card_count: int = 0) -> dict:
    return {
        "deck_id": deck.id,
        "name": deck.name,
        "description": deck.description,
        "featured": deck.featured,
        "owner_id": deck.owner_id,
        "created_by": deck.created_by,
        "created_at": deck.created_at.isoformat() if deck.created_at else None,
        "card_count": card_count,
    }


def _visible_decks_stmt(stmt, payload):
    """Public decks (owner NULL) + the caller's own; admins see all."""
    if _is_admin(payload):
        return stmt
    if payload and payload.get("authenticated"):
        return stmt.where(or_(Deck.owner_id.is_(None), Deck.owner_id == payload["user_id"]))
    return stmt.where(Deck.owner_id.is_(None))


def _can_modify_deck(deck: Deck, payload) -> bool:
    return _is_admin(payload) or (deck.owner_id and deck.owner_id == payload.get("user_id"))


@router.get("/decks")
def list_decks(db: Session = Depends(get_db), payload=Depends(get_current_user)):
    """Decks the caller may see (public + their own), with card counts."""
    counts = dict(
        db.execute(
            select(Card.deck_id, func.count())
            .where(Card.deck_id.is_not(None))
            .group_by(Card.deck_id)
        ).all()
    )
    decks = db.scalars(_visible_decks_stmt(select(Deck), payload).order_by(Deck.name))
    return {"decks": [_serialize_deck(d, counts.get(d.id, 0)) for d in decks]}


@router.get("/decks/{deck_id}")
def get_deck(deck_id: str, db: Session = Depends(get_db), payload=Depends(get_current_user)):
    deck = db.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    # Hide others' private decks.
    if deck.owner_id and not _is_admin(payload) and deck.owner_id != (payload or {}).get("user_id"):
        raise HTTPException(status_code=404, detail="Deck not found")
    count = db.scalar(select(func.count()).where(Card.deck_id == deck_id)) or 0
    return {"deck": _serialize_deck(deck, count)}


@router.post("/decks")
def create_deck(deck: DeckCreate, db: Session = Depends(get_db),
                payload=Depends(require_roles(["admin", "trusted"]))):
    """Admins create public decks; trusted users create their own private decks."""
    is_admin = _is_admin(payload)
    new_deck = Deck(
        name=deck.name,
        description=deck.description,
        featured=deck.featured if is_admin else False,   # only public decks can be featured
        owner_id=None if is_admin else payload["user_id"],
        created_by=payload["user_id"],
    )
    db.add(new_deck)
    db.commit()
    db.refresh(new_deck)
    return {"message": "Deck created", "deck_id": new_deck.id, "owner_id": new_deck.owner_id}


@router.put("/decks/{deck_id}")
def update_deck(deck_id: str, deck_update: DeckUpdate, db: Session = Depends(get_db),
                payload=Depends(require_authenticated)):
    """Update a deck — admins (any) or the owner of a private deck."""
    deck = db.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if not _can_modify_deck(deck, payload):
        raise HTTPException(status_code=403, detail="Not allowed")

    if deck_update.name is not None:
        deck.name = deck_update.name
    if deck_update.description is not None:
        deck.description = deck_update.description
    # Only admins control the public "featured" flag.
    if deck_update.featured is not None and _is_admin(payload):
        deck.featured = deck_update.featured
    db.commit()
    return {"message": "Deck updated"}


@router.delete("/decks/{deck_id}")
def delete_deck(deck_id: str, db: Session = Depends(get_db),
                payload=Depends(require_authenticated)):
    """Delete a deck — admins (any) or the owner. Cards are kept (deck_id -> NULL)."""
    deck = db.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if not _can_modify_deck(deck, payload):
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(deck)
    db.commit()
    return {"message": "Deck deleted"}
