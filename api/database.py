"""SQLAlchemy engine, session factory, and FastAPI dependency.

Postgres is the primary datastore for users, cards, and progress.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


def get_db():
    """Yield a request-scoped database session (FastAPI dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
