from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from db_models import Card, CardProposal, User
from models import ProposalCreate
from roles import require_authenticated, require_admin
from routes.cards import can_view_card

router = APIRouter()


def _serialize(p: CardProposal, card: Optional[Card] = None,
               proposer_email: Optional[str] = None) -> dict:
    return {
        "id": p.id,
        "card_id": p.card_id,
        "status": p.status,
        "note": p.note,
        "proposed": {"front": p.front, "back": p.back, "labels": list(p.labels or [])},
        # Current card values for side-by-side review (None if the card is gone).
        "current": None if card is None else {
            "front": card.front, "back": card.back, "labels": list(card.labels or []),
        },
        "proposer_email": proposer_email,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None,
    }


@router.post("/cards/{card_id}/proposals")
def create_proposal(card_id: str, body: ProposalCreate, db: Session = Depends(get_db),
                    payload=Depends(require_authenticated)):
    """Propose a change to a card the caller can see."""
    card = db.get(Card, card_id)
    if not card or not can_view_card(card, payload):
        raise HTTPException(status_code=404, detail="Card not found")

    proposal = CardProposal(
        card_id=card_id,
        proposer_id=payload["user_id"],
        front=body.front,
        back=body.back,
        labels=body.labels or [],
        note=body.note,
        status="pending",
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return {"message": "Proposal submitted", "id": proposal.id}


@router.get("/my-proposals")
def my_proposals(db: Session = Depends(get_db), payload=Depends(require_authenticated)):
    """The caller's proposals (all statuses), newest first."""
    rows = list(db.scalars(
        select(CardProposal)
        .where(CardProposal.proposer_id == payload["user_id"])
        .order_by(CardProposal.created_at.desc())
    ))
    cards = {c.id: c for c in db.scalars(select(Card).where(Card.id.in_([p.card_id for p in rows])))} if rows else {}
    return {"proposals": [_serialize(p, cards.get(p.card_id)) for p in rows]}


@router.get("/proposals", dependencies=[Depends(require_admin)])
def list_proposals(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Admin: review proposals, optionally filtered by status (default pending)."""
    stmt = select(CardProposal).order_by(CardProposal.created_at.desc())
    stmt = stmt.where(CardProposal.status == (status or "pending"))
    rows = list(db.scalars(stmt))
    cards = {c.id: c for c in db.scalars(select(Card).where(Card.id.in_([p.card_id for p in rows])))} if rows else {}
    emails = dict(db.execute(
        select(User.id, User.email).where(User.id.in_([p.proposer_id for p in rows]))
    ).all()) if rows else {}
    return {"proposals": [_serialize(p, cards.get(p.card_id), emails.get(p.proposer_id)) for p in rows]}


@router.post("/proposals/{proposal_id}/accept", dependencies=[Depends(require_admin)])
def accept_proposal(proposal_id: str, db: Session = Depends(get_db), payload=Depends(require_admin)):
    """Apply the proposed changes to the card and mark accepted."""
    proposal = db.get(CardProposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != "pending":
        raise HTTPException(status_code=400, detail="Proposal already reviewed")

    card = db.get(Card, proposal.card_id)
    if not card:
        raise HTTPException(status_code=400, detail="Card no longer exists")

    card.front = proposal.front
    card.back = proposal.back
    card.labels = list(proposal.labels or [])
    proposal.status = "accepted"
    proposal.reviewed_at = datetime.utcnow()
    proposal.reviewed_by = payload["user_id"]
    db.commit()
    return {"message": "Proposal accepted"}


@router.post("/proposals/{proposal_id}/reject", dependencies=[Depends(require_admin)])
def reject_proposal(proposal_id: str, db: Session = Depends(get_db), payload=Depends(require_admin)):
    proposal = db.get(CardProposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != "pending":
        raise HTTPException(status_code=400, detail="Proposal already reviewed")
    proposal.status = "rejected"
    proposal.reviewed_at = datetime.utcnow()
    proposal.reviewed_by = payload["user_id"]
    db.commit()
    return {"message": "Proposal rejected"}
