import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = os.environ.get('db_url', '')

if SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
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
