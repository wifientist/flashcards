"""SQLAlchemy engine, session factory, and FastAPI dependency.

Postgres is the primary datastore for users, cards, and progress.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DATABASE_URL

# Force the client connection to UTF-8. Without this, a database created with
# SQL_ASCII encoding makes psycopg2 use the ASCII codec, which raises
# UnicodeEncodeError on any non-ASCII text (em-dashes, smart quotes, accents,
# emoji). UTF-8 stores those losslessly even against a SQL_ASCII database.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    connect_args={"client_encoding": "utf8"},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


def get_db():
    """Yield a request-scoped database session (FastAPI dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
