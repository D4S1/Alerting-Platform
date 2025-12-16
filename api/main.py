from fastapi import FastAPI, HTTPException
from api.db import get_db
from api.schemas import ServiceCreate, AdminContactUpdate, ServiceAdminUpdate

app = FastAPI(title="Monitoring API")

@app.post("/services")
def add_service(service: ServiceCreate):
    with get_db() as db:
        db.execute(
            """
            INSERT INTO services (name, IP, frequency_seconds, alerting_window_seconds)
            VALUES (?, ?, ?, ?)
            """,
            (
                service.name,
                service.IP,
                service.frequency_seconds,
                service.alerting_window_seconds,
            ),
        )
    return {"status": "service added"}

@app.delete("/services/{service_id}")
def delete_service(service_id: int):
    with get_db() as db:
        cur = db.execute(
            "DELETE FROM services WHERE rowid = ?", (service_id,)
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Service not found")

        db.execute(
            "DELETE FROM service_admins WHERE service_id = ?", (service_id,)
        )
    return {"status": "service deleted"}

@app.put("/services/{service_id}/admin")
def change_service_admin(service_id: int, update: ServiceAdminUpdate):
    with get_db() as db:
        cur = db.execute(
            """
            UPDATE service_admins
            SET admin_id = ?
            WHERE service_id = ? AND role = ?
            """,
            (update.admin_id, service_id, update.role),
        )

        if cur.rowcount == 0:
            raise HTTPException(404, "Service or role not found")

    return {"status": "service admin updated"}

@app.patch("/admins/{admin_id}")
def update_admin_contact(admin_id: int, update: AdminContactUpdate):
    fields = []
    values = []

    if update.contact_type is not None:
        fields.append("contact_type = ?")
        values.append(update.contact_type)

    if update.contact_value is not None:
        fields.append("contact_value = ?")
        values.append(update.contact_value)

    if not fields:
        raise HTTPException(400, "No fields to update")

    values.append(admin_id)

    with get_db() as db:
        cur = db.execute(
            f"""
            UPDATE admins
            SET {', '.join(fields)}
            WHERE rowid = ?
            """,
            values,
        )

        if cur.rowcount == 0:
            raise HTTPException(404, "Admin not found")

    return {"status": "admin contact updated"}

