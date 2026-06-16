from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from database import get_db
from db_models import Card, Progress
from models import ReviewRequest
from roles import require_authenticated
from routes.cards import _serialize_card, can_view_card, label_match
import scheduler

router = APIRouter()


def _deck_id_list(deck_ids: Optional[str]):
    """Parse a comma-separated deck_ids param into a list, or None for 'all'."""
    if not deck_ids:
        return None
    ids = [d for d in deck_ids.split(",") if d]
    return ids or None


@router.get("/study/queue")
def study_queue(limit: int = 20, deck_id: Optional[str] = None,
                deck_ids: Optional[str] = None,
                labels: Optional[List[str]] = Query(None),
                db: Session = Depends(get_db),
                payload=Depends(require_authenticated)):
    """The caller's study queue, ordered new-first then by FSRS priority:
      1. up to `limit` NEW cards (never seen), shuffled — they jump the line.
      2. then ALL DUE cards (scheduled, due now), most-overdue first — so reviews
         never starve behind a backlog of new cards.
    Spans the given decks (comma-separated deck_ids, or single deck_id; omit for
    all) and, if `labels` is given, only cards carrying one of those labels. The
    label filter is applied *before* the new-card cap so chapter-scoped study
    doesn't starve behind unrelated new cards."""
    user_id = payload["user_id"]
    now = scheduler.now_utc()
    decks = _deck_id_list(deck_ids) or ([deck_id] if deck_id else None)
    # OR across labels: a card matches if it carries any selected label
    # (case-insensitive, via label_match).
    label_filter = or_(*[label_match(l) for l in labels]) if labels else None

    queue = []

    # 1) New cards (no progress yet), shuffled — these go first, capped at `limit`.
    tracked = set(db.scalars(
        select(Progress.card_id).where(Progress.user_id == user_id)
    ))
    new_conds = [or_(Card.owner_id.is_(None), Card.owner_id == user_id)]
    if decks is not None:
        new_conds.append(Card.deck_id.in_(decks))
    if label_filter is not None:
        new_conds.append(label_filter)
    if tracked:
        new_conds.append(Card.id.not_in(tracked))

    # Total untouched new cards in scope — lets the client offer "introduce more"
    # instead of falsely reporting "all caught up" when the cap held some back.
    new_available = db.scalar(select(func.count()).select_from(Card).where(*new_conds))

    new_stmt = select(Card).where(*new_conds).order_by(func.random()).limit(limit)
    new_count = 0
    for card in db.scalars(new_stmt):
        queue.append(_serialize_card(card, None, include_progress=True))
        new_count += 1

    # 2) Due cards (scheduled and due now), most-overdue first — always appended.
    due_stmt = (
        select(Progress)
        .join(Card, Card.id == Progress.card_id)
        .where(Progress.user_id == user_id,
               Progress.due.is_not(None),
               Progress.due <= now)
        .order_by(Progress.due.asc())
    )
    if decks is not None:
        due_stmt = due_stmt.where(Card.deck_id.in_(decks))
    if label_filter is not None:
        due_stmt = due_stmt.where(label_filter)
    due_progress = list(db.scalars(due_stmt))
    due_count = 0
    if due_progress:
        ids = [p.card_id for p in due_progress]
        cards_by_id = {c.id: c for c in db.scalars(select(Card).where(Card.id.in_(ids)))}
        pbc = {p.card_id: p for p in due_progress}
        for cid in ids:
            card = cards_by_id.get(cid)
            if card:
                queue.append(_serialize_card(card, pbc[cid], include_progress=True))
                due_count += 1

    return {
        "queue": queue,
        "count": len(queue),
        "new_count": new_count,
        "due_count": due_count,
        # New cards still untouched after this batch — drives the "introduce more" prompt.
        "new_remaining": max(0, new_available - new_count),
    }


@router.get("/study/marked")
def marked_cards(deck_id: Optional[str] = None, deck_ids: Optional[str] = None,
                 db: Session = Depends(get_db),
                 payload=Depends(require_authenticated)):
    """The caller's starred (flagged) cards, optionally scoped to deck(s)."""
    user_id = payload["user_id"]
    stmt = (
        select(Progress)
        .join(Card, Card.id == Progress.card_id)
        .where(Progress.user_id == user_id, Progress.flagged.is_(True))
    )
    decks = _deck_id_list(deck_ids) or ([deck_id] if deck_id else None)
    if decks is not None:
        stmt = stmt.where(Card.deck_id.in_(decks))
    rows = list(db.scalars(stmt))
    progress_by_card = {p.card_id: p for p in rows}
    ids = list(progress_by_card.keys())
    cards = list(db.scalars(select(Card).where(Card.id.in_(ids)))) if ids else []
    return {
        "cards": [
            _serialize_card(c, progress_by_card.get(c.id), include_progress=True)
            for c in cards
        ]
    }


@router.post("/cards/{card_id}/review")
def review_card(card_id: str, review: ReviewRequest, db: Session = Depends(get_db),
                payload=Depends(require_authenticated)):
    """Grade a card (again|hard|good|easy) and advance its FSRS schedule."""
    card = db.get(Card, card_id)
    if not card or not can_view_card(card, payload):
        raise HTTPException(status_code=404, detail="Card not found")

    user_id = payload["user_id"]
    progress = db.get(Progress, (user_id, card_id))
    if not progress:
        progress = Progress(user_id=user_id, card_id=card_id)
        db.add(progress)

    try:
        fsrs_card, due, status = scheduler.review(progress.fsrs_card, review.rating)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    progress.fsrs_card = fsrs_card
    progress.due = due
    progress.status = status
    progress.last_reviewed = datetime.utcnow()
    progress.review_count = (progress.review_count or 0) + 1

    db.commit()
    return {
        "message": "Review recorded",
        "due": due.isoformat(),
        "status": status,
        "review_count": progress.review_count,
    }
