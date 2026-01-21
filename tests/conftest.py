import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timezone, timedelta

from api.main import app
from api import db as db_module
from utils.models import Base, Service, Admin, ServiceAdmin

# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture(scope="function")
def db_session(tmp_path):
    """
    Creates a fresh SQLite file-based database in a temporary directory.
    """
    # File path for this test
    test_db_file = tmp_path / "test_monitoring.db"
    db_url = f"sqlite:///{test_db_file}"

    # Create engine and session factory
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Create tables
    Base.metadata.create_all(bind=engine)

    session: Session = TestingSessionLocal()
    try:
        # Pre-populate test data
        session.add_all([
            Admin(name="Alice", contact_type="email", contact_value="alice@test.com"),
            Admin(name="Bob", contact_type="email", contact_value="bob@test.com"),
            Admin(name="Hanna", contact_type="email", contact_value="hanna@test.com"),
            Admin(name="John", contact_type="email", contact_value="john@test.com"),
        ])
        session.add_all([
            Service(
                name="svc1",
                IP="1.1.1.1",
                frequency_seconds=1,          # very low for fast tests
                alerting_window_npings=3,     # threshold
                failure_threshold=2,          # new field
                next_at=datetime.now() + timedelta(minutes=5)
            ),
            Service(
                name="svc2",
                IP="1.1.1.2",
                frequency_seconds=1,
                alerting_window_npings=2,
                failure_threshold=1,
                next_at=datetime.now() + timedelta(minutes=5)
            ),
        ])
        session.commit()
        session.add_all([
            ServiceAdmin(service_id=1, admin_id=1, role="primary"),
            ServiceAdmin(service_id=1, admin_id=2, role="secondary"),
            ServiceAdmin(service_id=2, admin_id=3, role="primary"),
            ServiceAdmin(service_id=2, admin_id=4, role="secondary"),
        ])
        session.commit()

        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)  # Clean up tables


@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient that uses the SQLAlchemy session from db_session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[db_module.get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
