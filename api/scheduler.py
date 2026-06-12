"""Spaced-repetition scheduling, backed by the FSRS algorithm (py-fsrs).

We persist the FSRS card state as a JSON blob on the Progress row plus a
separate `due` timestamp for efficient "what's due now" queries. This wrapper
is the only place that imports `fsrs`, so swapping algorithms later is local.
"""
from datetime import datetime, timezone
from typing import Optional, Tuple

from fsrs import Scheduler, Card, Rating, State

# A single shared scheduler with default (well-tuned) parameters.
_scheduler = Scheduler()

# Map our API's rating strings to FSRS ratings.
_RATING_BY_NAME = {
    "again": Rating.Again,
    "hard": Rating.Hard,
    "good": Rating.Good,
    "easy": Rating.Easy,
}

# Human-friendly status derived from FSRS state, for display/filtering.
_STATUS_BY_STATE = {
    State.Learning: "learning",
    State.Review: "review",
    State.Relearning: "relearning",
}

VALID_RATINGS = tuple(_RATING_BY_NAME.keys())


def parse_rating(name: str) -> Rating:
    try:
        return _RATING_BY_NAME[name.lower()]
    except (KeyError, AttributeError):
        raise ValueError(f"Invalid rating {name!r}; expected one of {VALID_RATINGS}")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _load_card(fsrs_card: Optional[dict]) -> Card:
    """Rebuild an FSRS Card from stored JSON, or start a fresh one."""
    if fsrs_card:
        return Card.from_dict(fsrs_card)
    return Card()


def review(fsrs_card: Optional[dict], rating_name: str) -> Tuple[dict, datetime, str]:
    """Apply a review.

    Returns (new_fsrs_card_json, next_due_utc, derived_status).
    """
    card = _load_card(fsrs_card)
    rating = parse_rating(rating_name)
    card, _log = _scheduler.review_card(card, rating, review_datetime=now_utc())
    status = _STATUS_BY_STATE.get(card.state, "review")
    return card.to_dict(), card.due, status
