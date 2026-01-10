import pytest
import sqlite3
import jwt
from datetime import datetime, timedelta
from notification_module.notifications import JWT_SECRET


# -----------------------------
# Test helpers
# -----------------------------

def make_token(incident_id=1, admin_id=1, expired=False):
    payload = {
        "incident_id": incident_id,
        "admin_id": admin_id,
        "exp": datetime.utcnow() - timedelta(minutes=1)
        if expired
        else datetime.utcnow() + timedelta(minutes=10),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# -----------------------------
# Tests
# -----------------------------

def test_acknowledge_incident_success(client, test_db):
    token = make_token(incident_id=1, admin_id=1)

    response = client.get(f"/incidents/ack?token={token}")

    assert response.status_code == 200
    assert response.json()["status"] == "acknowledged"

    # sprawdzenie DB
    with sqlite3.connect(test_db) as conn:
        status = conn.execute(
            "SELECT status FROM incidents WHERE id = 1"
        ).fetchone()[0]

        assert status == "acknowledged"

def test_acknowledge_idempotent(client):
    token = make_token(incident_id=1, admin_id=1)

    r1 = client.get(f"/incidents/ack?token={token}")
    r2 = client.get(f"/incidents/ack?token={token}")

    assert r1.json()["status"] == "acknowledged"
    assert r2.json()["status"] == "already acknowledged"

def test_acknowledge_resolved_incident(client, test_db):
    with sqlite3.connect(test_db) as conn:
        conn.execute(
            "UPDATE incidents SET status = 'resolved' WHERE id = 1"
        )
        conn.commit()

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

def test_contact_attempt_updated_on_ack(client, test_db):
    token = make_token(incident_id=1, admin_id=1)

    client.get(f"/incidents/ack?token={token}")

    with sqlite3.connect(test_db) as conn:
        row = conn.execute("""
            SELECT result, response_at
            FROM contact_attempts
            WHERE incident_id = 1 AND admin_id = 1
        """).fetchone()

        assert row is not None
        assert row[0] == "acknowledged"
        assert row[1] is not None
