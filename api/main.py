from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session, joinedload
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
import os
from pydantic import BaseModel

from api.db import get_db, engine
from utils.models import Base
from api.schemas import ServiceCreate, ServiceEdit, AdminContactUpdate, ServiceAdminCreate, ServiceAdminUpdate, AdminCreate, ServiceOut, AdminOut, ContactAttemptCreate, AckRequest, ContactAttemptOut
from utils.models import Service, Admin, ServiceAdmin, Incident, PingFailure, ContactAttempt

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)  # Create tables if not present
    except Exception as e:
        print(f"Error initialising database:: {e}")
    yield


app = FastAPI(title="Monitoring API", lifespan=lifespan)

JWT_SECRET = os.environ.get('jwt_secret', 'test-secret-key')


# -----------------------------
# Services
# -----------------------------

@app.post("/services")
def add_service(service: ServiceCreate, db: Session = Depends(get_db)):
    new_service = Service(
        name=service.name,
        IP=service.IP,
        frequency_seconds=service.frequency_seconds,
        alerting_window_npings=service.alerting_window_npings,
        failure_threshold=service.failure_threshold,
        next_at=datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=1)
    )
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return {"status": "service added", "service_id": new_service.id}


@app.get("/services/due", response_model=list[ServiceOut])
def get_due_services(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc).replace(microsecond=0)

    services = (
        db.query(Service)
        .filter(Service.next_at <= now)
        .with_for_update()
        .all()
    )
    for svc in services:
        svc.next_at = now + timedelta(seconds=svc.frequency_seconds)

    db.commit()
    return services


@app.get("/services/{service_id}")
def get_service(service_id: int, db: Session = Depends(get_db)):
    existing_service = db.query(Service).filter(Service.id == service_id).first()
    if not existing_service:
        raise HTTPException(status_code=404, detail="Service not found")

    return existing_service


@app.put("/services/{service_id}")
def edit_service(service_id: int, service: ServiceEdit, db: Session = Depends(get_db)):
    existing_service = db.query(Service).filter(Service.id == service_id).first()
    if not existing_service:
        raise HTTPException(status_code=404, detail="Service not found")

    existing_service.frequency_seconds = service.frequency_seconds
    existing_service.alerting_window_npings = service.alerting_window_npings
    existing_service.failure_threshold = service.failure_threshold

    db.commit()
    db.refresh(existing_service)
    return {"status": "service updated", "service_id": existing_service.id}


@app.delete("/services/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(404, "Service not found")

    db.delete(service)
    db.commit()
    return {"status": "service deleted"}

# -----------------------------
# Service admins
# -----------------------------

@app.post("/services/{service_id}/admin")
def create_service_admin(service_id: int, admin_data: ServiceAdminCreate, db: Session = Depends(get_db)):
    
    existing = db.query(ServiceAdmin).filter(
        ServiceAdmin.service_id == service_id,
        ServiceAdmin.role == admin_data.role
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Service admin for this role already exists")

    sa = ServiceAdmin(
        service_id=service_id,
        admin_id=admin_data.admin_id,
        role=admin_data.role
    )
    db.add(sa)
    db.commit()
    db.refresh(sa)
    return {"status": "service admin created", "service_admin": sa}


@app.get("/services/{service_id}/admins", response_model=dict[str, AdminOut])
def get_service_admin(service_id: int, db: Session = Depends(get_db)):

    admins = db.query(ServiceAdmin).filter(ServiceAdmin.service_id == service_id).all()
    admins = {a.role: db.query(Admin).filter(Admin.id == a.admin_id).first() for a in admins}
    return admins


@app.put("/services/{service_id}/admin")
def update_service_admin(service_id: int, update: ServiceAdminUpdate, db: Session = Depends(get_db)):
    sa = db.query(ServiceAdmin).filter(
        ServiceAdmin.service_id == service_id,
        ServiceAdmin.role == update.role
    ).first()

    if not sa:
        raise HTTPException(status_code=404, detail="Service admin with given service ID and role not found")

    # Check if new admin is already assigned to this service
    existing = db.query(ServiceAdmin).filter(
        ServiceAdmin.service_id == service_id,
        ServiceAdmin.admin_id == update.new_admin_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Admin already assigned to this service"
        )

    sa.admin_id = update.new_admin_id
    db.commit()
    db.refresh(sa)
    return {"status": "service admin updated", "service_admin": sa}

# -----------------------------
# Admins
# -----------------------------

@app.post("/admins/", response_model=AdminOut)
def create_admin(admin: AdminCreate, db: Session = Depends(get_db)):
    existing_admin = db.query(Admin).filter(
        Admin.contact_type == admin.contact_type,
        Admin.contact_value == admin.contact_value
    ).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")

    # Create new admin
    new_admin = Admin(
        name=admin.name,
        contact_type=admin.contact_type,
        contact_value=admin.contact_value
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin


@app.patch("/admins/{admin_id}")
def update_admin_contact(admin_id: int, update: AdminContactUpdate, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(404, "Admin not found")

    if update.contact_type is not None:
        admin.contact_type = update.contact_type
    if update.contact_value is not None:
        admin.contact_value = update.contact_value

    if update.contact_type is None and update.contact_value is None:
        raise HTTPException(400, "No fields to update")

    db.commit()
    db.refresh(admin)
    return {"status": "admin contact updated"}


@app.get("/admins/", response_model=list[AdminOut])
def get_all_admins(db: Session = Depends(get_db)):
    return db.query(Admin).all()


@app.get("/admins/contact/{value}", response_model=AdminOut)
def get_admin_by_contact(value: str, db: Session = Depends(get_db)):

    admin = db.query(Admin).filter(Admin.contact_value == value).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin


@app.get("/admins/{admin_id}/services", response_model=list[ServiceOut])
def get_services_for_admin(admin_id: int, db: Session = Depends(get_db)):
    # Check if admin exists first (optional, but good for error handling)
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    # Query Services joined with ServiceAdmin where admin_id matches
    services = (
        db.query(Service)
        .join(ServiceAdmin)
        .filter(ServiceAdmin.admin_id == admin_id)
        .all()
    )
    
    return services

# -----------------------------
# Incidents
# -----------------------------

@app.post("/services/{service_id}/incidents")
def add_incident(service_id: int, db: Session = Depends(get_db)):
    incident = Incident(service_id=service_id)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident

@app.get("/services/{service_id}/incidents")
def list_service_incidents(service_id: int, db: Session = Depends(get_db)):
    return db.query(Incident).filter(Incident.service_id == service_id).all()


@app.get("/services/{service_id}/incidents/open")
def list_open_incidents_for_service(service_id: int, db: Session = Depends(get_db)):
    return db.query(Incident).filter(
        Incident.service_id == service_id,
        Incident.status.in_(["registered", "acknowledged"])
    ).all()


@app.patch("/incidents/{incident_id}/status")
def update_incident_status(incident_id: int, status: str, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(404, "Incident not found")

    incident.status = status
    db.commit()
    db.refresh(incident)
    return incident


@app.patch("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(404, "Incident not found")

    incident.ended_at = datetime.now(timezone.utc)
    incident.status = "resolved"
    db.commit()
    db.refresh(incident)
    return incident


@app.get("/incidents/{incident_id}/admins")
def get_incident_admins(incident_id: int, role: str | None = None, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(404, "Incident not found")
    q = (
        db.query(Admin)
        .join(ServiceAdmin, ServiceAdmin.admin_id == Admin.id)
        .filter(ServiceAdmin.service_id == incident.service_id)
    )
    if role:
        q = q.filter(ServiceAdmin.role == role)
    return q.all()


@app.get("/incidents/{incident_id}/notified-admins")
def get_notified_admins(incident_id: int, db: Session = Depends(get_db)):
    admins = (
        db.query(Admin)
        .join(ContactAttempt, ContactAttempt.admin_id == Admin.id)
        .filter(ContactAttempt.incident_id == incident_id)
        .distinct()
        .all()
    )
    return admins


@app.post("/incidents/ack") 
def acknowledge_incident(request: AckRequest, db: Session = Depends(get_db)):
    token = request.token
    
    # Decode token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")

    incident_id = payload["incident_id"]
    admin_id = payload["admin_id"]

    # Fetch incident
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Handle terminal states
    if incident.status == "resolved":
        return {"status": "already resolved"}

    if incident.status == "acknowledged":
        return {"status": "already acknowledged"}

    # Acknowledge incident
    incident.status = "acknowledged"
    db.commit()

    # Update contact attempt
    attempt = db.query(ContactAttempt).filter(
        ContactAttempt.incident_id == incident_id,
        ContactAttempt.admin_id == admin_id
    ).order_by(ContactAttempt.attempted_at.desc()).first()

    if attempt:
        attempt.result = "acknowledged"
        attempt.response_at = datetime.now(timezone.utc)
        db.commit()

    return {"status": "acknowledged"}


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(404, "Incident not found")
    return incident


# -----------------------------
# Failures
# -----------------------------

@app.post("/services/{service_id}/failures")
def record_ping_failure(service_id: int, db: Session = Depends(get_db)):
    failure = PingFailure(service_id=service_id)
    db.add(failure)
    db.commit()
    return {"status": "failure recorded"}


@app.get("/services/{service_id}/failures/recent")
def list_recent_failures(service_id: int, window_seconds: int, db: Session = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)

    return (
        db.query(PingFailure)
        .filter(PingFailure.service_id == service_id)
        .filter(PingFailure.failed_at >= cutoff)
        .all()
    )


@app.delete("/failures/cleanup")
def cleanup_old_failures(db: Session = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    deleted = db.query(PingFailure).filter(PingFailure.failed_at < cutoff).delete()
    db.commit()
    return {"deleted": deleted}

# -----------------------------
# Contact attempts
# -----------------------------

@app.post("/contact_attempts/")
def add_contact_attempt(contact_attempt: ContactAttemptCreate, db: Session = Depends(get_db)):
    new_attempt = ContactAttempt(
        incident_id=contact_attempt.incident_id,
        admin_id=contact_attempt.admin_id,
        channel=contact_attempt.channel,
        attempted_at=datetime.now(timezone.utc),
        result=None,
        response_at=None
    )
    db.add(new_attempt)
    db.commit()
    db.refresh(new_attempt)

    return {"status": "contact attempt added", "contact_attempt_id": new_attempt.id}

@app.patch("/contact_attempts/{attempt_id}")
def update_contact_attempt(attempt_id: int, result: str, db: Session = Depends(get_db)):
    attempt = db.query(ContactAttempt).filter(ContactAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(404, "Contact attempt not found")

    attempt.result = result
    attempt.response_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(attempt)
    return attempt
    c

@app.get("/contact_attempts", response_model=list[ContactAttemptOut])
def get_contact_attempts(service_id: int, db: Session = Depends(get_db)):
    attempts = (
        db.query(ContactAttempt)
        .join(Incident)
        .options(joinedload(ContactAttempt.admin)) 
        .filter(Incident.service_id == service_id)
        .all()
    )

    for a in attempts:
        a.admin_name = a.admin.name
        
    return attempts
