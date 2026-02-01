import time
import asyncio
import json
import httpx
from google.cloud import pubsub_v1
from utils.auth import get_headers_async

class IPStatusCollector:

    def __init__(self, service: dict, api_base_url: str, pubsub_topic: str, publisher=None):
        self.service = service
        self.api_base_url = api_base_url.rstrip("/")
        self.pubsub_topic = pubsub_topic
        self.publisher = publisher or pubsub_v1.PublisherClient()

        self.alerting_window_seconds = (
            self.service["alerting_window_npings"]
            * self.service["frequency_seconds"]
        )

    async def run_once(self):
        success = await self._perform_check()

        if not success:
            await self._record_failure()

        should_trigger = await self._should_trigger_incident()
        open_incident = await self._get_open_incident()

        if should_trigger and not open_incident:
            incident = await self._create_incident()
            await self._publish_incident(incident["id"])

        if not should_trigger and open_incident:
            await self._resolve_incident(open_incident["id"])

    # ------------------ Ping ------------------

    async def _perform_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.service['IP']}")
                return r.status_code < 400
        except Exception:
            return False

    # ------------------ Failures (DB) ------------------

    async def _record_failure(self):
        url = f"{self.api_base_url}/services/{self.service['id']}/failures"
        headers = await get_headers_async(self.api_base_url)
        
        async with httpx.AsyncClient() as client:
            await client.post(url, headers=headers)

    async def _should_trigger_incident(self) -> bool:
        url = f"{self.api_base_url}/services/{self.service['id']}/failures/recent"
        params = {"window_seconds": self.alerting_window_seconds}
        headers = await get_headers_async(self.api_base_url)

        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, headers=headers)
            if r.status_code != 200:
                print(f"API Error in _should_trigger_incident: {r.status_code}")
                return False
                
            failures = r.json()
            return len(failures) >= self.service["failure_threshold"]

    # ------------------ Incidents (API) ------------------

    async def _get_open_incident(self):
        url = f"{self.api_base_url}/services/{self.service['id']}/incidents/open"
        headers = await get_headers_async(self.api_base_url)

        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                return None
            incidents = r.json()
            return incidents[0] if incidents else None

    async def _create_incident(self):
        url = f"{self.api_base_url}/services/{self.service['id']}/incidents"
        headers = await get_headers_async(self.api_base_url)

        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers)
            return r.json()

    async def _resolve_incident(self, incident_id: int):
        # Resolve via API
        url = f"{self.api_base_url}/incidents/{incident_id}/resolve"
        headers = await get_headers_async(self.api_base_url)

        async with httpx.AsyncClient() as client:
            r = await client.patch(url, headers=headers)
            resolved_incident = r.json()

        # Send Pub/Sub notification
        message = {
            "type": "RESOLVE_INCIDENT",
            "service_id": self.service["id"],
            "incident_id": incident_id,
            "timestamp": time.time(),
        }
        data = json.dumps(message).encode("utf-8")
        future = self.publisher.publish(self.pubsub_topic, data)
        await asyncio.wrap_future(future)

        return resolved_incident

    # ------------------ Pub/Sub ------------------

    async def _publish_incident(self, incident_id: int):
        message = {
            "type": "CREATE_INCIDENT",
            "service_id": self.service["id"],
            "incident_id": incident_id,
            "timestamp": time.time(),
        }

        data = json.dumps(message).encode("utf-8")
        future = self.publisher.publish(self.pubsub_topic, data)
        await asyncio.wrap_future(future)
