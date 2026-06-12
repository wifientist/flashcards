"""Pytest configuration and shared fixtures.

Test env is set BEFORE importing the app (config.py validates at import time).
Tests run against a real Postgres + Redis — provide them via env:

    DATABASE_URL  (default: localhost:5432/flashcards)
    REDIS_URL_0   (default: redis://localhost:6379/15 — a throwaway DB index)

Each test starts with truncated tables and a flushed Redis DB.
"""
import os

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-a-placeholder-0123456789")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://flashcards:flashcards@localhost:5432/flashcards",
)
os.environ.setdefault("REDIS_URL_0", "redis://localhost:6379/15")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5177")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

import main  # noqa: E402
from database import engine, Base, SessionLocal  # noqa: E402
import db_models  # noqa: F401,E402  (register models on Base.metadata)
from db_models import User  # noqa: E402
from jwt_utils import hash_password  # noqa: E402
from redis_client import r0  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_state():
    """Fresh DB + Redis before every test."""
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    r0.flushdb()
    yield


def _create_user(email: str, password: str, roles=None) -> str:
    db = SessionLocal()
    try:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            roles=roles or ["user"],
            is_active=True,
        )
        db.add(user)
        db.commit()
        return user.id
    finally:
        db.close()


@pytest.fixture
def client():
    """Unauthenticated client."""
    with TestClient(main.app) as c:
        yield c


@pytest.fixture
def admin():
    """A logged-in admin client (own cookie jar)."""
    _create_user("admin@test.com", "adminpw123", roles=["user", "admin"])
    c = TestClient(main.app)
    resp = c.post("/auth/login", json={"email": "admin@test.com", "password": "adminpw123"})
    assert resp.status_code == 200, resp.text
    return c


@pytest.fixture
def user():
    """A logged-in regular user client (own cookie jar)."""
    _create_user("user@test.com", "userpw123", roles=["user"])
    c = TestClient(main.app)
    resp = c.post("/auth/login", json={"email": "user@test.com", "password": "userpw123"})
    assert resp.status_code == 200, resp.text
    return c


@pytest.fixture
def trusted():
    """A logged-in trusted (non-admin) user who can create private cards."""
    _create_user("trusted@test.com", "pw1234567", roles=["user", "trusted"])
    c = TestClient(main.app)
    resp = c.post("/auth/login", json={"email": "trusted@test.com", "password": "pw1234567"})
    assert resp.status_code == 200, resp.text
    return c


@pytest.fixture
def make_card(admin):
    def _make(front="front", back="back", labels=None, deck_id=None):
        r = admin.post("/cards", json={
            "front": front, "back": back, "labels": labels or [], "deck_id": deck_id,
        })
        assert r.status_code == 200, r.text
        return r.json()["card_id"]
    return _make


@pytest.fixture
def make_deck(admin):
    def _make(name="Deck", description=None):
        r = admin.post("/decks", json={"name": name, "description": description})
        assert r.status_code == 200, r.text
        return r.json()["deck_id"]
    return _make
