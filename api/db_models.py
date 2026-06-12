"""SQLAlchemy ORM models — the relational schema.

UUID primary keys are stored as strings to match the app's existing uuid4
identifiers and keep things portable. Labels are stored as a Postgres text
array on the card (global, free-form strings), matching the prior design.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, ForeignKey,
)
from sqlalchemy.dialects.postgresql import ARRAY
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

    cards = relationship("Card", back_populates="creator")
    progress = relationship(
        "Progress", back_populates="user", cascade="all, delete-orphan"
    )


class Card(Base):
    __tablename__ = "cards"

    id = Column(String, primary_key=True, default=_uuid)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    labels = Column(ARRAY(String), nullable=False, default=list)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    creator = relationship("User", back_populates="cards")
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

    user = relationship("User", back_populates="progress")
    card = relationship("Card", back_populates="progress")
