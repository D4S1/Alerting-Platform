import time
import jwt
from datetime import datetime, timedelta, timezone

from api_client import NotificationApiClient
from config import JWTConfig
from notification_module.mailer import Mailer
from utils.models import Admin

JWT_SECRET = JWTConfig.SECRET
JWT_EXP_MINUTES = JWTConfig.EXP_MINUTES
ESCALATION_DELAY_SECONDS = 300  # 5 minutes


class NotificationEngine:
    """
    Handles incident-related notifications and escalation logic.

    The NotificationEngine reacts to incident lifecycle events (creation and resolution),
    notifies appropriate administrators via email, generates acknowledgment tokens,
    records contact attempts, and escalates incidents if they are not acknowledged
    within a defined time window.

    Attributes:
        db: Database interface used to fetch incidents, administrators, and store contact attempts.
        mailer: Mailer service responsible for sending email notifications.
    """

    def __init__(self, api: NotificationApiClient, mailer: Mailer):
        """
        :param db: Database access layer.
        :param mailer: Mailer service used to send emails.
        """
        self.api = api
        self.mailer = mailer

    def handle_event(self, event: dict):
        """
        Sends the event to the appropriate internal handler based on its type.
        """
        if event["type"] == "CREATE_INCIDENT":
            self._handle_incident_created(event["incident_id"])
        elif event["type"] == "RESOLVE_INCIDENT":
            self._handle_incident_resolved(event["incident_id"])

    def _handle_incident_created(self, incident_id: int):
        """
        Notifies primary administrators associated with the affected service
        of the newly created incident.
        """
        primary_admins = self.api.get_admins_by_incident(
            incident_id,
            role="primary"
        )

        for admin in primary_admins:
            self._notify_admin(incident_id, admin, escalation=False)

    def _notify_admin(self, incident_id: int, admin: Admin, escalation: bool):
        """
        Generates an acknowledgment token, sends a notification email to the admin,
        records the contact attempt, and schedules escalation if required.
        """
        token = self._generate_ack_token(
            incident_id=incident_id,
            admin_id=admin.id
        )

        service_name = self.api.get_service_name(incident_id)
        service_str = f" {service_name}" if service_name else ""

        link = f"https://monitoring.local/ack/{token}"

        success = self.mailer.send(
            to=admin.contact_value,
            subject="Incident detected",
            body=f"Service{service_str} is DOWN.\n\n{link}"
        )

        self.api.add_contact_attempt({
            "incident_id": incident_id,
            "admin_id": admin.id,
            "channel": "email",
            "result": "sent" if success else "failed"
        })

        if not escalation:
            self._schedule_escalation(incident_id)

    def _generate_ack_token(self, incident_id: int, admin_id: int) -> str:
        """
        Generate a JWT acknowledgment token for an administrator.
        The token encodes the incident ID, administrator ID, and expiration time.
        """
        payload = {
            "incident_id": incident_id,
            "admin_id": admin_id,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXP_MINUTES),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    def _schedule_escalation(self, incident_id: int):
        """
        Waits for a predefined delay, checks whether the incident was acknowledged,
        and if not, notifies secondary administrators.
        """
        time.sleep(ESCALATION_DELAY_SECONDS)
        # In production: replace sleep with delayed job / scheduler / Celery task

        if self.api.is_acknowledged(incident_id):
            return

        secondary_admins = self.api.get_admins_by_incident(
            incident_id,
            role="secondary"
        )

        for admin in secondary_admins:
            self._notify_admin(incident_id, admin, escalation=True)

    def _handle_incident_resolved(self, incident_id: int):
        """
        Sends a resolution notification to all administrators
        who were previously notified about the incident.
        """
        admins = self.api.get_notified_admins(incident_id)

        for admin in admins:
            self.mailer.send(
                to=admin.contact_value,
                subject="Incident resolved",
                body="The service is back online."
            )


    def _handle_incident_resolved(self, incident_id: int):
        """
        Sends a resolution notification to all administrators
        who were previously notified about the incident.
        """
        admins = self.db.get_notified_admins(incident_id)

        for admin in admins:
            self.mailer.send(
                to=admin.contact_value,
                subject="Incident resolved",
                body="The service is back online."
            )
