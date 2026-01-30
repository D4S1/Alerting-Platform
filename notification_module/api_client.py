import requests

class NotificationApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get_incident(self, incident_id: int):
        return requests.get(
            f"{self.base_url}/incidents/{incident_id}"
        ).json()

    def get_admins_by_incident(self, incident_id: int, role: str):
        return requests.get(
            f"{self.base_url}/incidents/{incident_id}/admins",
            params={"role": role}
        ).json()

    def get_service_name(self, incident_id: int):
        r = requests.get(
            f"{self.base_url}/incidents/{incident_id}/service"
        ).json()
        return r["service_name"]

    def is_acknowledged(self, incident_id: int) -> bool:
        r = requests.get(
            f"{self.base_url}/incidents/{incident_id}/acknowledged"
        ).json()
        return r["acknowledged"]

    def add_contact_attempt(self, payload: dict):
        requests.post(
            f"{self.base_url}/contact_attempts/",
            json=payload
        )

    def get_notified_admins(self, incident_id: int):
        return requests.get(
            f"{self.base_url}/incidents/{incident_id}/notified-admins"
        ).json()
