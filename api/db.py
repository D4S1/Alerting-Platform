import sqlite3
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DB_PATH = "database/test.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite-specific
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """
    Provides a SQLAlchemy Session for ORM endpoints.
    Use this with FastAPI Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
