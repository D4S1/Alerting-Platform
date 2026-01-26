import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, ANY
from config import JWTConfig
from utils.models import Admin, Incident, ContactAttempt
from notification_module.notification_engine import NotificationEngine


# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture
def mock_mailer():
    mailer = MagicMock()
    mailer.send.return_value = True
    return mailer


# -----------------------------
# Test helpers
# -----------------------------

def make_token(incident_id=1, admin_id=1, expired=False):
    payload = {
        "incident_id": incident_id,
        "admin_id": admin_id,
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1)
        if expired
        else datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, JWTConfig.SECRET, algorithm="HS256")


# -----------------------------
# Tests
# -----------------------------

def test_acknowledge_incident_success(client, db_session):
    token = make_token(incident_id=1, admin_id=1)

    response = client.get(f"/incidents/ack?token={token}")

    assert response.status_code == 200
    assert response.json()["status"] == "acknowledged"

    incident = (
        db_session.query(Incident)
        .filter_by(id=1)
        .first()
    )

    assert incident.status == "acknowledged"

def test_acknowledge_idempotent(client):
    token = make_token(incident_id=1, admin_id=1)

    r1 = client.get(f"/incidents/ack?token={token}")
    r2 = client.get(f"/incidents/ack?token={token}")

    assert r1.json()["status"] == "acknowledged"
    assert r2.json()["status"] == "already acknowledged"

def test_acknowledge_resolved_incident(client, db_session):
    incident = (
        db_session.query(Incident)
        .filter_by(id=1)
        .first()
    )
    incident.status = "resolved"
    db_session.commit()

    token = make_token(incident_id=1, admin_id=1)
    response = client.get(f"/incidents/ack?token={token}")

    assert response.json()["status"] == "already resolved"

def test_acknowledge_expired_token(client):
    token = make_token(expired=True)

    response = client.get(f"/incidents/ack?token={token}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Token expired"

def test_acknowledge_invalid_token(client):
    response = client.get("/incidents/ack?token=not-a-jwt")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid token"

def test_contact_attempt_updated_on_ack(client, db_session):
    token = make_token(incident_id=1, admin_id=1)

    client.get(f"/incidents/ack?token={token}")

    attempt = (
        db_session.query(ContactAttempt)
        .filter_by(incident_id=1, admin_id=1)
        .first()
    )

    assert attempt is not None
    assert attempt.result == "acknowledged"
    assert attempt.response_at is not None

def test_notification_engine_logic(mock_mailer):
    api = MagicMock()
    fake_admin = Admin(id=1, contact_value="test@example.com") # Fake admin as API response
    api.get_admins_by_incident.return_value = [fake_admin]
    
    engine = NotificationEngine(api=api, mailer=mock_mailer)
    engine.handle_event({"type": "CREATE_INCIDENT", "incident_id": 123})
    assert mock_mailer.send.called  # Test if send was called

    mock_mailer.send.assert_called_once_with(
        to="test@example.com",
        subject="Incident detected",
        body=ANY
    )