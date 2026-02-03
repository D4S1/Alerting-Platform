from utils.models import Service, Admin, ServiceAdmin, Incident
from datetime import datetime, timezone, timedelta
from tests.conftest import make_ack_token


# -----------------------------
# Services
# -----------------------------

def test_add_service(client, db_session):
    resp = client.post(
        "/services",
        json={
            "name": "new-service",
            "IP": "8.8.8.8",
            "frequency_seconds": 30,
            "alerting_window_npings": 10,
            "failure_threshold": 5,
        },
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "service added"

    # Verify via SQLAlchemy session
    service = db_session.query(Service).filter_by(name="new-service").first()
    assert service is not None
    assert service.IP == "8.8.8.8"
    assert service.frequency_seconds == 30
    assert service.alerting_window_npings == 10
    assert service.failure_threshold == 5

def test_get_service(client):
    resp = client.get("/services/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["name"] == "svc1"

def test_get_missing_service(client):
    resp = client.get("/services/999")
    assert resp.status_code == 404

def test_get_due_services(client, db_session):
    
    svc = db_session.get(Service, 1)
    svc.next_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    db_session.commit()

    resp = client.get("/services/due")
    print(resp.json())
    assert resp.status_code == 200

    services = resp.json()
    assert len(services) == 1
    assert services[0]["id"] == 1

def test_edit_service(client, db_session):
    resp = client.put(
        "/services/1",
        json={
            "frequency_seconds": 120,
            "alerting_window_npings": 500,
            "failure_threshold": 10,
        },
    )

    assert resp.status_code == 200

    svc = db_session.get(Service, 1)
    assert svc.frequency_seconds == 120
    assert svc.alerting_window_npings == 500
    assert svc.failure_threshold == 10

def test_delete_service(client, db_session):
    # Delete service via endpoint
    resp = client.delete("/services/2")
    assert resp.status_code == 200
    assert resp.json()["status"] == "service deleted"

    # Verify deletion in DB
    service = db_session.query(Service).filter_by(id=2).first()
    assert service is None

# -----------------------------
# Service admins
# -----------------------------

def test_create_service_admin(client, db_session):
    service = Service(name="Test service", IP="7.7.7.7", frequency_seconds=60, alerting_window_npings=5, failure_threshold=3)
    admin = Admin(name='Henry', contact_type='email', contact_value="henry@test.com")

    db_session.add_all([service, admin])
    db_session.commit()

    resp = client.post(
        f"/services/{service.id}/admin",
        json={
            "admin_id": admin.id,
            "role": "secondary"
        }
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "service admin created"

def test_create_service_admin_conflict(client):
    resp = client.post(
        "/services/1/admin",
        json={
            "admin_id": 3,
            "role": "primary"
        }
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Service admin for this role already exists"


def test_get_service_admins(client):
    resp = client.get("/services/1/admins")
    assert resp.status_code == 200

    data = resp.json()
    assert "primary" in data
    assert data["primary"]["name"] == "Alice"


def test_update_service_admin(client, db_session):
    resp = client.put(
        "/services/1/admin",
        json={
            "role": "primary",
            "new_admin_id": 3
        },
    )
    assert resp.status_code == 200

    sa = db_session.query(ServiceAdmin).filter_by(
        service_id=1, role="primary"
    ).first()
    assert sa.admin_id == 3

def test_update_service_admin_conflict(client):
    resp = client.put(
        "/services/1/admin",
        json={
            "role": "primary",
            "new_admin_id": 2  # already exists as secondary
        },
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Admin already assigned to this service"

# -----------------------------
# Admins
# -----------------------------

def test_create_admin(client):
    resp = client.post(
        "/admins/",
        json={
            "name": "Kate",
            "contact_type": "email",
            "contact_value": "kate@test.com"
        }
    )

    assert resp.status_code == 200
    assert resp.json()["name"] == "Kate"

def test_update_admin_contact(client, db_session):
    resp = client.patch(
        "/admins/1",
        json={
            "contact_value": "alice_new@test.com",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "admin contact updated"

    admin = db_session.query(Admin).filter_by(id=1).first()
    assert admin.contact_value == "alice_new@test.com"

def test_update_missing_admin(client):
    resp = client.patch(
        "/admins/999",
        json={"contact_value": "x@test.com"},
    )
    assert resp.status_code == 404

def test_update_admin_no_fields(client):
    resp = client.patch("/admins/1", json={})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "No fields to update"

def test_get_all_admins(client):
    resp = client.get("/admins/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 4

def test_get_admin_by_contact(client):
    resp = client.get("/admins/contact/alice@test.com")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alice"

def test_get_services_for_admin(client):
    resp = client.get("/admins/1/services")
    assert resp.status_code == 200

    services = resp.json()
    assert len(services) == 1
    assert services[0]["name"] == "svc1"

# -----------------------------
# Incidents
# -----------------------------

def test_get_incident(client):
    resp = client.get("/incidents/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1

def test_add_incident(client, db_session):
    resp = client.post("/services/1/incidents")
    assert resp.status_code == 200

    inc = db_session.query(Incident).order_by(Incident.id.desc()).first()
    assert inc.service_id == 1

def test_list_service_incidents(client):
    resp = client.get("/services/1/incidents")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

def test_list_open_incidents_for_service(client):
    resp = client.get("/services/1/incidents/open")
    assert resp.status_code == 200
    assert resp.json()[0]["status"] in ["registered", "acknowledged"]

def test_update_incident_status(client):
    resp = client.patch("/incidents/1/status?status=acknowledged")
    assert resp.status_code == 200
    assert resp.json()["status"] == "acknowledged"

def test_resolve_incident(client):
    resp = client.patch("/incidents/1/resolve")
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"

def test_get_incident_admins(client):
    resp = client.get("/incidents/1/admins")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

def test_get_notified_admins(client):
    resp = client.get("/incidents/1/notified-admins")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_acknowledge_incident(client, db_session):
    token = make_ack_token(incident_id=1, admin_id=1)

    resp = client.post(f"/incidents/ack", json={'token': token})
    assert resp.status_code == 200
    assert resp.json()["status"] == "acknowledged"

    inc = db_session.get(Incident, 1)
    assert inc.status == "acknowledged"

def test_acknowledge_resolved_incident(client, db_session):
    inc = db_session.get(Incident, 1)
    inc.status = "resolved"
    db_session.commit()

    token = make_ack_token(1, 1)

    resp = client.post(f"/incidents/ack", json={'token': token})
    assert resp.status_code == 200
    assert resp.json()["status"] == "already resolved"


# -----------------------------
# Failures
# -----------------------------

def test_record_ping_failure(client):
    resp = client.post("/services/1/failures")
    assert resp.status_code == 200
    assert resp.json()["status"] == "failure recorded"

def test_list_recent_failures(client):
    client.post("/services/1/failures")

    resp = client.get("/services/1/failures/recent?window_seconds=60")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert resp.json()[0]["service_id"] == 1

def test_cleanup_old_failures(client):
    resp = client.delete("/failures/cleanup")
    assert resp.status_code == 200
    assert "deleted" in resp.json()

# -----------------------------
# Contact attempts
# -----------------------------

def test_add_contact_attempt(client):
    resp = client.post(
        "/contact_attempts/",
        json={
            "incident_id": 1,
            "admin_id": 1,
            "channel": "email"
        }
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "contact attempt added"

def test_update_contact_attempt(client):
    resp = client.patch("/contact_attempts/1?result=acknowledged")
    assert resp.status_code == 200
    assert resp.json()["result"] == "acknowledged"
