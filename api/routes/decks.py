from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database import get_db
from db_models import Deck, Card
from models import DeckCreate, DeckUpdate
from roles import require_roles

router = APIRouter()


def _serialize_deck(deck: Deck, card_count: int = 0) -> dict:
    return {
        "deck_id": deck.id,
        "name": deck.name,
        "description": deck.description,
        "created_by": deck.created_by,
        "created_at": deck.created_at.isoformat() if deck.created_at else None,
        "card_count": card_count,
    }


@router.get("/decks")
def list_decks(db: Session = Depends(get_db)):
    """All decks with their card counts (public)."""
    counts = dict(
        db.execute(
            select(Card.deck_id, func.count())
            .where(Card.deck_id.is_not(None))
            .group_by(Card.deck_id)
        ).all()
    )
    decks = db.scalars(select(Deck).order_by(Deck.name))
    return {"decks": [_serialize_deck(d, counts.get(d.id, 0)) for d in decks]}


@router.get("/decks/{deck_id}")
def get_deck(deck_id: str, db: Session = Depends(get_db)):
    deck = db.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    count = db.scalar(select(func.count()).where(Card.deck_id == deck_id)) or 0
    return {"deck": _serialize_deck(deck, count)}


@router.post("/decks")
def create_deck(deck: DeckCreate, db: Session = Depends(get_db),
                payload=Depends(require_roles(["admin"]))):
    """Create a deck - admin only."""
    new_deck = Deck(
        name=deck.name,
        description=deck.description,
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
    db.commit()
    return {"message": "Deck updated"}


@router.delete("/decks/{deck_id}")
def delete_deck(deck_id: str, db: Session = Depends(get_db),
                payload=Depends(require_roles(["admin"]))):
    """Delete a deck - admin only. Cards are kept (deck_id set to NULL)."""
    deck = db.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    db.delete(deck)
    db.commit()
    return {"message": "Deck deleted"}
