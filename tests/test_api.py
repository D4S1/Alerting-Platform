from utils.models import Service, Admin, ServiceAdmin

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


def test_delete_service(client, db_session):
    # Delete service via endpoint
    resp = client.delete("/services/2")
    assert resp.status_code == 200
    assert resp.json()["status"] == "service deleted"

    # Verify deletion in DB
    service = db_session.query(Service).filter_by(id=2).first()
    assert service is None

    service_admins = db_session.query(ServiceAdmin).filter_by(service_id=2).all()
    assert len(service_admins) == 0


def test_change_service_admin(client, db_session):
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

def test_change_service_admin_conflict(client):
    resp = client.put(
        "/services/1/admin",
        json={
            "role": "primary",
            "new_admin_id": 2  # already exists as secondary
        },
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Admin already assigned to this service"


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

