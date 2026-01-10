from fastapi import FastAPI, HTTPException, Depends
from api.db import get_database
from api.schemas import ServiceCreate, AdminContactUpdate, ServiceAdminUpdate
from database.db import Database
import jwt
from datetime import datetime
from notification_module.notifications import JWT_SECRET

app = FastAPI(title="Monitoring API")


@app.post("/services")
def add_service(
    service: ServiceCreate,
    db: Database = Depends(get_database),
):
    db.add_service(service)
    return {"status": "service added"}


@app.delete("/services/{service_id}")
def delete_service(
    service_id: int,
    db: Database = Depends(get_database),
):
    deleted = db.delete_service(service_id)
    if not deleted:
        raise HTTPException(404, "Service not found")

    return {"status": "service deleted"}


@app.put("/services/{service_id}/admin")
def change_service_admin(
    service_id: int,
    update: ServiceAdminUpdate,
    db: Database = Depends(get_database),
):
    updated = db.update_service_admin(
        service_id=service_id,
        admin_id=update.admin_id,
        role=update.role,
    )

    if not updated:
        raise HTTPException(404, "Service or role not found")

    return {"status": "service admin updated"}


@app.patch("/admins/{admin_id}")
def update_admin_contact(
    admin_id: int,
    update: AdminContactUpdate,
    db: Database = Depends(get_database),
):
    updated = db.update_admin_contact(
        admin_id=admin_id,
        contact_type=update.contact_type,
        contact_value=update.contact_value,
    )

    if not updated:
        raise HTTPException(404, "Admin not found")

    return {"status": "admin contact updated"}


@app.get("/ack/{token}")
def acknowledge(
    token: str,
    db: Database = Depends(get_database),
):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(400, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(400, "Invalid token")

    status = db.acknowledge_incident(
        incident_id=payload["incident_id"],
        admin_id=payload["admin_id"],
        response_at=datetime.utcnow(),
    )

    return {"status": status}
