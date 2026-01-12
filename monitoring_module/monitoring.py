import time
import requests
from collections import deque
from typing import Deque


class IPStatusCollector:

    """
    Monitors the availability of a specified IP or URL by performing periodic HTTP GET requests.
    Tracks failures over a sliding time window and triggers an incident if the number of failures
    exceeds a defined threshold. Incident information is published via a provided queue publisher.

    Attributes:
        ip (str): IP address or URL to monitor.
        frequency (int): Interval in seconds between status checks.
        alerting_window (int): Time window in seconds over which failures are counted.
        failure_threshold (int): Number of failures within the alerting window that triggers an alert.
        timeout (float): Timeout in seconds for each HTTP GET request.
        queue_publisher: An object responsible for publishing incident jobs.
        failures (Deque[float]): Timestamps of recorded failures within the alerting window.

    Methods:
        run_once(): Performs a single status check and handles failure recording and incident publishing.
        run_forever(): Continuously monitors the target IP/URL at the specified frequency.
    """

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
        self.alerting_window = alerting_window * frequency
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
            return response.status_code < 400
        except requests.RequestException as e:
            return False

    def _record_failure(self):
        """Record the timestamp of a failure."""
        now = time.time()
        self.failures.append(now)
        self._cleanup_old_failures(now)

    def _cleanup_old_failures(self, now: float):
        """Remove failures outside the alerting_window."""
        while self.failures and now - self.failures[0] > self.alerting_window:
            self.failures.popleft()

    def _should_trigger_incident(self) -> bool:
        return len(self.failures) >= self.failure_threshold

    def _publish_incident(self):
        # with internall IP check if incident already exists for self.ip with status == registered/acknowledged
        # if yes do not publish a new one
        # if no create a new one api query to add incident
        # if incident is None:
        job = {
            "type": "CREATE_INCIDENT",
            "service_id": self.ip,
            "started_at": time.time(),
            'status': 'registered',
        }
        self.queue_publisher.publish(job) # query API to create incident

    def _check_existing_incident(self):
        # Placeholder for checking existing incidents
        # In a real implementation, this would query a API
        # get incidents for self.ip with status registered/acknowledged
        # return incident if exists else None
        return None

    def run_once(self):
        """Perform a single status check."""
        success = self._perform_check()
        # if success and incident exists for self.ip with status registered/acknowledged, resolve it
        if success:
            # Check if an incident exists for this IP
            existing_incident = self._check_existing_incident()
            if existing_incident and existing_incident['status'] in ['registered', 'acknowledged']:
                self._resolve_incident(existing_incident)
        else:
            self._record_failure()
            if self._should_trigger_incident():
                self._publish_incident()

