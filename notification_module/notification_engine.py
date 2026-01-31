import json
import jwt
from google.cloud import tasks_v2
from datetime import datetime, timedelta, timezone
from google.protobuf import timestamp_pb2

from config import JWTConfig
from notification_module.api_client import NotificationApiClient
from notification_module.mailer import Mailer
from utils.models import Admin


class NotificationEngine:
    """
    Handles incident-related notifications and escalation logic.

    The NotificationEngine reacts to incident lifecycle events (creation and resolution),
    notifies appropriate administrators via email, generates acknowledgment tokens,
    records contact attempts, and escalates incidents if they are not acknowledged
    within a defined time window.

    Attributes:
        api: API client used to interact with the notification backend.
        mailer: Mailer service responsible for sending email notifications.
        project_id: GCP project ID for Cloud Tasks.
        location: GCP location for Cloud Tasks.
        queue: Cloud Tasks queue name.
    """
    def __init__(self, api: NotificationApiClient, mailer: Mailer, project_id: str, location: str, queue: str):
        self.api = api
        self.mailer = mailer
        self.tasks_client = tasks_v2.CloudTasksClient()
        
        # Cloud Tasks configuration
        self.queue_path = self.tasks_client.queue_path(project_id, location, queue)
        self.service_url = "https://cloud-run-service.a.run.app/escalate" # TODO: replace with actual URL

    def handle_event(self, event: dict):
        """
        Sends the event to the appropriate internal handler based on its type.
        """
        if event["type"] == "CREATE_INCIDENT":
            return self._handle_incident_created(event["incident_id"])
        elif event["type"] == "RESOLVE_INCIDENT":
            return self._handle_incident_resolved(event["incident_id"])

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
        }
        return jwt.encode(payload, JWTConfig.JWT_SECRET, algorithm="HS256")

    def _schedule_escalation(self, incident_id: int):
        """
        Creates a task in Cloud Tasks that hits the /escalate endpoint after the delay.
        """
        
        payload = {"incident_id": incident_id}
        body = json.dumps(payload).encode()

        # Calculate scheduled time
        d = datetime.now(timezone.utc) + timedelta(seconds=JWTConfig.ESCALATION_DELAY_SECONDS)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": self.service_url,
                "headers": {"Content-type": "application/json"},
                "body": body,
            },
            "schedule_time": timestamp,
        }

        self.tasks_client.create_task(parent=self.queue_path, task=task)
        print(f"Scheduled escalation for incident {incident_id}")


    def handle_escalation_check(self, incident_id: int):
        """
        Sends escalation notifications to secondary administrators
        if the incident has not been acknowledged.
        """

        if self.api.is_acknowledged(incident_id):
            print(f"Incident {incident_id} already acknowledged. Skipping escalation.")
            return

        secondary_admins = self.api.get_admins_by_incident(incident_id, role="secondary")
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