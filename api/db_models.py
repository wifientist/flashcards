"""SQLAlchemy ORM models — the relational schema.

UUID primary keys are stored as strings to match the app's existing uuid4
identifiers and keep things portable. Labels are stored as a Postgres text
array on the card (global, free-form strings), matching the prior design.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Index, text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    roles = Column(ARRAY(String), nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    # Persisted per-user study scope: which decks to span in the study queue.
    # Empty = all decks.
    study_deck_ids = Column(ARRAY(String), nullable=False, default=list, server_default="{}")

    # cards has two FKs to users (created_by, owner_id) — disambiguate.
    cards = relationship("Card", back_populates="creator", foreign_keys="Card.created_by")
    progress = relationship(
        "Progress", back_populates="user", cascade="all, delete-orphan"
    )


class Deck(Base):
    __tablename__ = "decks"
    # At most one private deck per owner (public decks have NULL owner_id).
    __table_args__ = (
        Index("uq_decks_owner", "owner_id", unique=True,
              postgresql_where=text("owner_id IS NOT NULL")),
    )

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    # When true, this deck's cards appear in the public (unauthenticated) landing.
    featured = Column(Boolean, nullable=False, default=False, server_default="false")
    # NULL = public (admin) deck. Set = private deck owned by that user.
    owner_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    cards = relationship("Card", back_populates="deck")


class Card(Base):
    __tablename__ = "cards"

    id = Column(String, primary_key=True, default=_uuid)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    labels = Column(ARRAY(String), nullable=False, default=list)
    deck_id = Column(
        String, ForeignKey("decks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # NULL = public (admin-created). Set = private card owned by that user.
    owner_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    creator = relationship("User", back_populates="cards", foreign_keys=[created_by])
    deck = relationship("Deck", back_populates="cards")
    progress = relationship(
        "Progress", back_populates="card", cascade="all, delete-orphan"
    )


class Progress(Base):
    __tablename__ = "progress"

    # Composite primary key: one progress row per (user, card).
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    card_id = Column(
        String, ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True
    )
    notes = Column(Text, nullable=False, default="")
    status = Column(String, nullable=False, default="new")
    last_reviewed = Column(DateTime, nullable=True)
    review_count = Column(Integer, nullable=False, default=0)
    # User-set star/flag, independent of FSRS status (never auto-overwritten).
    flagged = Column(Boolean, nullable=False, default=False, server_default="false")

    # FSRS scheduling state. `due` is denormalized out of `fsrs_card` for fast
    # "what's due now" queries; `fsrs_card` is the serialized FSRS Card.
    due = Column(DateTime(timezone=True), nullable=True, index=True)
    fsrs_card = Column(JSONB, nullable=True)

    user = relationship("User", back_populates="progress")
    card = relationship("Card", back_populates="progress")


class CardProposal(Base):
    """A user-proposed change to a card's content, reviewed by an admin.
    Stored separately so it never mutates the card until accepted."""
    __tablename__ = "card_proposals"

    id = Column(String, primary_key=True, default=_uuid)
    card_id = Column(String, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True)
    proposer_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Proposed values (a complete suggested version of the card).
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    labels = Column(ARRAY(String), nullable=False, default=list)
    note = Column(Text, nullable=True)            # optional rationale
    status = Column(String, nullable=False, default="pending", server_default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
