import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
import os
import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timezone, timedelta

from api.main import app
from api import db as db_module
from utils.models import Base, Service, Admin, ServiceAdmin, Incident, ContactAttempt


# -----------------------------
# Pytest Configuration
# -----------------------------

def pytest_configure(config):
    """
    Sets environment variables for tests.
    """
    os.environ["JWT_SECRET"] = "test-secret-key"
    os.environ["SMTP_HOST"] = "localhost"
    os.environ["SMTP_USERNAME"] = "test-user"
    os.environ["SMTP_PASSWORD"] = "test-password"
    os.environ["SMTP_PORT"] = "587"

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
        # Admins
        admins=[
            Admin(name="Alice", contact_type="email", contact_value="alice@test.com"),
            Admin(name="Bob", contact_type="email", contact_value="bob@test.com"),
            Admin(name="Hanna", contact_type="email", contact_value="hanna@test.com"),
            Admin(name="John", contact_type="email", contact_value="john@test.com"),
        ]
        services = [
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
        ]
        session.add_all(services)
        session.add_all(admins)
        session.commit()

        # ServiceAdmins
        session.add_all([
            ServiceAdmin(service_id=services[0].id, admin_id=admins[0].id, role="primary"),
            ServiceAdmin(service_id=services[0].id, admin_id=admins[1].id, role="secondary"),
            ServiceAdmin(service_id=services[1].id, admin_id=admins[2].id, role="primary"),
            ServiceAdmin(service_id=services[1].id, admin_id=admins[3].id, role="secondary"),
        ])
        session.commit()

        # Incidents
        incident = Incident(
            service_id=services[0].id,
            status="registered"
        )
        session.add(incident)
        session.commit()
        session.refresh(incident)

        # ContactAttempts
        attempt = ContactAttempt(
            incident_id=incident.id,
            admin_id=admins[0].id,
            channel="email",
            attempted_at=datetime.now(timezone.utc),
            result="sent",
            response_at=None
        )
        session.add(attempt)
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

# -----------------------------
# Test helpers
# -----------------------------

def make_ack_token(incident_id=1, admin_id=1, jwt_secret="test-secret-key"):
    payload = {
        "incident_id": incident_id,
        "admin_id": admin_id,
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")