import asyncio
import os
import httpx
from collector import IPStatusCollector

POLL_INTERVAL = 1  # seconds


class MonitoringEngine:

    def __init__(self, api_base_url: str, pubsub_topic: str):
        self.api_base_url = api_base_url.rstrip("/")
        self.pubsub_topic = pubsub_topic

    async def fetch_due_services(self):
        url = f"{self.api_base_url}/services/due"
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.json()

    async def run(self):
        while True:
            try:
                services = await self.fetch_due_services()
                print(services)
                tasks = [
                    IPStatusCollector(
                        service=s,
                        api_base_url=self.api_base_url,
                        pubsub_topic=self.pubsub_topic,
                    ).run_once()
                    for s in services
                ]

                if tasks:
                    await asyncio.gather(*tasks)

            except Exception as e:
                print("Monitoring loop error:", e) #faile

            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    api_base_url = 'http://127.0.0.1:8000' #os.environ["API_BASE_URL"]      # http://api:8080
    pubsub_topic = 'projects/x/topics/incidents' #os.environ["PUBSUB_TOPIC"]     # projects/x/topics/incidents

    engine = MonitoringEngine(api_base_url, pubsub_topic)
    asyncio.run(engine.run())
