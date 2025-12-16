import time
import requests
from collections import deque
from typing import Deque


class IPStatusCollector:
    def __init__(
        self,
        ip: str,
        frequency: int,
        alerting_window: int,
        failure_threshold: int,
        timeout: float,
        queue_publisher,
    ):
        """
        :param ip: IP or URL to monitor
        :param frequency: frequency of checks (seconds)
        :param alerting_window: time window in ping number
        :param failure_threshold: number of failures in the window that triggers an alert
        :param timeout: timeout for HTTP GET
        :param queue_publisher: object responsible for publishing jobs
        """
        self.ip = ip
        self.frequency = frequency
        self.alerting_window = alerting_window
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.queue_publisher = queue_publisher

        self.failures: Deque[float] = deque()

    def _perform_check(self) -> bool:
        """Do the HTTP GET and return True if successful."""
        try:
            response = requests.get(
                f"http://{self.ip}",
                timeout=self.timeout,
            )
            return response.status_code < 500
        except requests.RequestException:
            return False

    def _record_failure(self):
        """Record the timestamp of a failure."""
        now = time.time()
        self.failures.append(now)
        self._cleanup_old_failures(now)

    def _cleanup_old_failures(self, now: float):
        """Remove failures outside the alerting_window."""
        # implement failure cleanup logic
        pass

    def _should_trigger_incident(self) -> bool:
        # implement incident triggering logic
        return len(self.failures) >= self.failure_threshold

    def _publish_incident(self):
        job = {
            "type": "CREATE_INCIDENT",
            "service_id": self.ip,
            "started_at": time.time(),
            'status': 'registered',
        }
        self.queue_publisher.publish(job)

    def run_once(self):
        """Perform a single status check."""
        success = self._perform_check()

        if not success:
            self._record_failure()
            if self._should_trigger_incident():
                self._publish_incident()

    def run_forever(self):
        """Continuous monitoring loop."""
        while True:
            self.run_once()
            time.sleep(self.frequency)
