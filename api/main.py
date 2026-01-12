from fastapi import FastAPI, HTTPException, Depends
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from api.db import get_db
from api.schemas import ServiceCreate, AdminContactUpdate, ServiceAdminUpdate
from utils.models import Service, Admin, ServiceAdmin, Incident

app = FastAPI(title="Monitoring API")


@app.post("/services")
def add_service(service: ServiceCreate, db: Session = Depends(get_db)):
    new_service = Service(
        name=service.name,
        IP=service.IP,
        frequency_seconds=service.frequency_seconds,
        alerting_window_npings=service.alerting_window_npings
    )
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return {"status": "service added", "service_id": new_service.id}


@app.delete("/services/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(404, "Service not found")

    # Delete related service_admins
    db.query(ServiceAdmin).filter(ServiceAdmin.service_id == service_id).delete()
    db.delete(service)
    db.commit()
    return {"status": "service deleted"}


@app.put("/services/{service_id}/admin")
def change_service_admin(service_id: int, update: ServiceAdminUpdate, db: Session = Depends(get_db)):
    sa = db.query(ServiceAdmin).filter(
        ServiceAdmin.service_id == service_id,
        ServiceAdmin.role == update.role
    ).first()

    if not sa:
        raise HTTPException(404, "Service or role not found")

    sa.admin_id = update.admin_id
    db.commit()
    db.refresh(sa)
    return {"status": "service admin updated"}


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


@app.get("/services/{service_id}/incidents")
def list_service_incidents(service_id: int, db: Session = Depends(get_db)):
    return db.query(Incident).filter(Incident.service_id == service_id).all()


@app.get("/services/{service_id}/incidents/open")
def list_open_incidents_for_service(service_id: int, db: Session = Depends(get_db)):
    return db.query(Incident).filter(
        Incident.service_id == service_id,
        Incident.status.in_(["registered", "acknowledged"])
    ).all()


@app.post("/services/{service_id}/incidents")
def create_incident(service_id: int, db: Session = Depends(get_db)):
    incident = Incident(service_id=service_id)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


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
def update_incident_ended_at(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(404, "Incident not found")

    incident.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incident)
    return incident
