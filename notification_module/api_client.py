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
        # Get incident, to find service id
        r_incident = requests.get(
            f"{self.api_base_url}/incidents/{incident_id}",
            headers=get_headers(self.api_base_url)
        )
        
        if r_incident.status_code != 200:
            print(f"Failed to fetch incident {incident_id}: {r_incident.text}")
            return "Unknown Service"
            
        incident_data = r_incident.json()
        service_id = incident_data.get("service_id")
        
        if not service_id:
            return "Unknown Service"

        # Get service name by id
        r_service = requests.get(
            f"{self.api_base_url}/services/{service_id}",
            headers=get_headers(self.api_base_url)
        )
        
        if r_service.status_code != 200:
            print(f"Failed to fetch service {service_id}: {r_service.text}")
            return "Unknown Service"
            
        return r_service.json().get("name", "Unknown Service")

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
