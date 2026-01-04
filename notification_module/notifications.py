import time
import jwt
from datetime import datetime, timedelta

JWT_SECRET = "super-secret"
JWT_EXP_MINUTES = 15
ESCALATION_DELAY_SECONDS = 300  # 5 min


class NotificationEngine:
    def __init__(self, db, mailer):
        self.db = db
        self.mailer = mailer

    def handle_event(self, event: dict):
        if event["type"] == "CREATE_INCIDENT":
            self._handle_incident_created(event["incident_id"])
        elif event["type"] == "RESOLVE_INCIDENT":
            self._handle_incident_resolved(event["incident_id"])

    def _handle_incident_created(self, incident_id: int):
        incident = self.db.get_incident(incident_id)
        primary_admins = self.db.get_admins(
            incident.service_id,
            role="primary"
        )

        for admin in primary_admins:
            self._notify_admin(
                incident_id,
                admin,
                escalation=False
            )
    
    def _notify_admin(self, incident_id, admin, escalation: bool):
        token = self._generate_ack_token(
            incident_id=incident_id,
            admin_id=admin.id
        )

        link = f"https://monitoring.local/ack/{token}"

        subject = "Incident detected"
        body = f"""
        Service is DOWN.

        Click to acknowledge:
        {link}

        This link expires in {JWT_EXP_MINUTES} minutes.
        """

        success = self.mailer.send(
            to=admin.contact_value,
            subject=subject,
            body=body
        )

        self.db.insert_contact_attempt(
            incident_id=incident_id,
            admin_id=admin.id,
            channel="email",
            result="sent" if success else "failed",
            attempted_at=datetime.utcnow()
        )

        if not escalation:
            self._schedule_escalation(incident_id)

    def _generate_ack_token(self, incident_id: int, admin_id: int) -> str:
        payload = {
            "incident_id": incident_id,
            "admin_id": admin_id,
            "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    def _schedule_escalation(self, incident_id: int):
        time.sleep(ESCALATION_DELAY_SECONDS)  # in production: delayed job/cron/Celery instead of sleep

        if self.db.is_incident_acknowledged(incident_id):
            return

        secondary_admins = self.db.get_admins_by_incident(
            incident_id,
            role="secondary"
        )

        for admin in secondary_admins:
            self._notify_admin(
                incident_id,
                admin,
                escalation=True
            )
    
    def _handle_incident_resolved(self, incident_id: int):
        admins = self.db.get_notified_admins(incident_id)

        for admin in admins:
            self.mailer.send(
                to=admin.contact_value,
                subject="Incident resolved",
                body="The service is back online."
            )




