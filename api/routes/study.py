from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from db_models import Card, Progress
from models import ReviewRequest
from roles import require_authenticated
from routes.cards import _serialize_card
import scheduler

router = APIRouter()


@router.get("/study/queue")
def study_queue(limit: int = 20, db: Session = Depends(get_db),
                payload=Depends(require_authenticated)):
    """The caller's study queue: cards due now (most overdue first), then new
    (never-seen) cards, up to `limit`."""
    user_id = payload["user_id"]
    now = scheduler.now_utc()

    # Cards that are scheduled and currently due.
    due_progress = list(db.scalars(
        select(Progress)
        .where(Progress.user_id == user_id,
               Progress.due.is_not(None),
               Progress.due <= now)
        .order_by(Progress.due.asc())
    ))
    progress_by_card = {p.card_id: p for p in due_progress}
    due_ids = [p.card_id for p in due_progress]

    cards_by_id = {}
    if due_ids:
        cards_by_id = {c.id: c for c in db.scalars(select(Card).where(Card.id.in_(due_ids)))}

    queue = []
    for cid in due_ids:  # preserve due-order
        card = cards_by_id.get(cid)
        if card:
            queue.append(_serialize_card(card, progress_by_card[cid], include_progress=True))
        if len(queue) >= limit:
            break

    # Backfill with new cards (no progress row yet).
    if len(queue) < limit:
        tracked = set(db.scalars(
            select(Progress.card_id).where(Progress.user_id == user_id)
        ))
        new_stmt = select(Card)
        if tracked:
            new_stmt = new_stmt.where(Card.id.not_in(tracked))
        for card in db.scalars(new_stmt):
            queue.append(_serialize_card(card, None, include_progress=True))
            if len(queue) >= limit:
                break

    return {"queue": queue, "count": len(queue), "due_count": len(due_ids)}


@router.post("/cards/{card_id}/review")
def review_card(card_id: str, review: ReviewRequest, db: Session = Depends(get_db),
                payload=Depends(require_authenticated)):
    """Grade a card (again|hard|good|easy) and advance its FSRS schedule."""
    if not db.get(Card, card_id):
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
