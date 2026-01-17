import pytest
import jwt
from datetime import datetime, timedelta, timezone
from config import JWTConfig
from utils.models import Incident, ContactAttempt
from notification_module.mailer import Mailer


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

def mailer_setup(email="aniaszymik02@gmail.com", subject="Test", body="This is a test email."):
    mock_mailer = Mailer()
    mock_mailer.send(email, subject, body)
    return mock_mailer


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
