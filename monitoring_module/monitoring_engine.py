import os
import asyncio
import httpx
from google.cloud import pubsub_v1
from collector import IPStatusCollector

# Polling interval in seconds
POLL_INTERVAL = 1


class MonitoringEngine:

    def __init__(self, api_base_url: str, pubsub_topic: str):
        self.api_base_url = api_base_url.rstrip("/")
        self.pubsub_topic = pubsub_topic
        # Initialize Pub/Sub client
        self.publisher = pubsub_v1.PublisherClient()

    async def fetch_due_services(self):
        url = f"{self.api_base_url}/services/due"
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url)
            r.raise_for_status()
            return await r.json()

    async def run_once(self):
        try:
            services = await self.fetch_due_services()
            tasks = [
                IPStatusCollector(
                    service=s,
                    api_base_url=self.api_base_url,
                    pubsub_topic=self.pubsub_topic,
                    publisher=self.publisher,
                ).run_once()
                for s in services
            ]

            if tasks:
                await asyncio.gather(*tasks)

        except Exception as e:
            print("Monitoring loop error:", e)

    async def run(self):
        while True:
            await self.run_once()
            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    # Cloud Run Job env vars
    api_base_url = os.environ["API_BASE_URL"]
    pubsub_topic = os.environ["PUBSUB_TOPIC"]

    engine = MonitoringEngine(api_base_url, pubsub_topic)
    asyncio.run(engine.run())
