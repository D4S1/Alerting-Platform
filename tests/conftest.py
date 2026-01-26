import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timezone

from api.main import app
from api import db as db_module
from utils.models import Base, Service, Admin, ServiceAdmin, Incident, ContactAttempt

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
        admins = [
            Admin(name="Alice", contact_type="email", contact_value="alice@test.com"),
            Admin(name="Bob", contact_type="email", contact_value="bob@test.com"),
            Admin(name="Hanna", contact_type="email", contact_value="hanna@test.com"),
            Admin(name="John", contact_type="email", contact_value="john@test.com"),
        ]
        session.add_all(admins)

        # Services
        services = [
            Service(name="svc1", IP="1.1.1.1", frequency_seconds=60, alerting_window_npings=300),
            Service(name="svc2", IP="1.1.1.2", frequency_seconds=20, alerting_window_npings=200),
        ]
        session.add_all(services)
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

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """
    Env variables for testing.
    """
    monkeypatch.setenv("SMTP_HOST", "localhost")
    monkeypatch.setenv("SMTP_USERNAME", "test")
    monkeypatch.setenv("SMTP_PASSWORD", "test")
    monkeypatch.setenv("SMTP_FROM", "test@test.com")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("JWT_SECRET", "test-secret-key")
    monkeypatch.setenv("JWT_EXP_MINUTES", "15")
    monkeypatch.setenv("ESCALATION_DELAY_SECONDS", "1")