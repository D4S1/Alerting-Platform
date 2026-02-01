import requests
from utils.auth import get_headers

class NotificationApiClient:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url.rstrip("/")

    def get_incident(self, incident_id: int):
        return requests.get(
            f"{self.api_base_url}/incidents/{incident_id}",
            headers=get_headers(self.api_base_url)
        ).json()

    def get_admins_by_incident(self, incident_id: int, role: str):
        return requests.get(
            f"{self.api_base_url}/incidents/{incident_id}/admins",
            params={"role": role},
            headers=get_headers(self.api_base_url)
        ).json()

    def get_service_name(self, incident_id: int):
        r = requests.get(
            f"{self.api_base_url}/incidents/{incident_id}/service",
            headers=get_headers(self.api_base_url)
        ).json()
        return r["service_name"]

    def is_acknowledged(self, incident_id: int) -> bool:
        r = requests.get(
            f"{self.api_base_url}/incidents/{incident_id}/acknowledged",
            headers=get_headers(self.api_base_url)
        ).json()
        return r["acknowledged"]

    def add_contact_attempt(self, payload: dict):
        requests.post(
            f"{self.api_base_url}/contact_attempts/",
            json=payload,
            headers=get_headers(self.api_base_url)
        )

    def get_notified_admins(self, incident_id: int):
        return requests.get(
            f"{self.api_base_url}/incidents/{incident_id}/notified-admins",
            headers=get_headers(self.api_base_url)
        ).json()
