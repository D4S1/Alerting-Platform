import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_NAME = os.environ["DB_NAME"]
DB_HOST = os.environ["DB_HOST"]
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

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
