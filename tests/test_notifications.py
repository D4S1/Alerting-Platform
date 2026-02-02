import pytest
from unittest.mock import MagicMock
from flask import Flask

from utils.models import Admin, Incident, ContactAttempt
from notification_module.notification_engine import NotificationEngine
from tests.conftest import make_ack_token

# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture
def mock_mailer():
    mailer = MagicMock()
    mailer.send.return_value = True
    return mailer

@pytest.fixture
def mock_tasks_client(monkeypatch):
    mock_client = MagicMock()

    monkeypatch.setattr(
        "notification_module.notification_engine.tasks_v2.CloudTasksClient",
        lambda: mock_client
    )
    return mock_client


# -----------------------------
# Tests
# -----------------------------

def test_acknowledge_incident_success(client, db_session):
    token = make_ack_token(incident_id=1, admin_id=1)

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
    token = make_ack_token(incident_id=1, admin_id=1)

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

    token = make_ack_token(incident_id=1, admin_id=1)
    response = client.get(f"/incidents/ack?token={token}")

    assert response.json()["status"] == "already resolved"

def test_acknowledge_invalid_token(client):
    response = client.get("/incidents/ack?token=not-a-jwt")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid token"

def test_contact_attempt_updated_on_ack(client, db_session):
    token = make_ack_token(incident_id=1, admin_id=1)

    client.get(f"/incidents/ack?token={token}")

    attempt = (
        db_session.query(ContactAttempt)
        .filter_by(incident_id=1, admin_id=1)
        .first()
    )

    assert attempt is not None
    assert attempt.result == "acknowledged"
    assert attempt.response_at is not None

def test_notification_engine_logic(mock_mailer, mock_tasks_client):
    api = MagicMock()
    api.get_admins_by_incident.return_value = [{'id': 1, 'contact_value': "test@example.com"}]
    api.get_service_name.return_value = None

    engine = NotificationEngine(
        api=api,
        mailer=mock_mailer,
        esc_delay_seconds=1
    )

    # Mock http request context
    app = Flask(__name__)
    with app.test_request_context(base_url="https://test-host"):
        engine.handle_event({"type": "CREATE_INCIDENT", "incident_id": 123})

    mock_mailer.send.assert_called_once()
    mock_tasks_client.create_task.assert_called_once()

    args, kwargs = mock_tasks_client.create_task.call_args
    created_task = kwargs['task']
    # Check that the URL in the task contains the test host
    assert "https://test-host/escalate" == created_task['http_request']['url']
