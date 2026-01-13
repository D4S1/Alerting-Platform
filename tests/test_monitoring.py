import time
import pytest
from unittest.mock import patch
from requests import RequestException
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout

from monitoring_module.monitoring import IPStatusCollector


# -----------------------------
# Fake queue publisher
# -----------------------------
class FakeQueuePublisher:
    def __init__(self):
        self.jobs = []

    def publish(self, job):
        self.jobs.append(job)


# -----------------------------
# Test helpers
# -----------------------------
def create_collector(
    *,
    failure_threshold=3,
    alerting_window=10,
):
    return IPStatusCollector(
        ip="1.1.1.1",
        frequency=10,
        alerting_window=alerting_window,
        failure_threshold=failure_threshold,
        timeout=1,
        queue_publisher=FakeQueuePublisher(),
    )


# -----------------------------
# Tests: _perform_check
# -----------------------------
def test_check_success():
    collector = create_collector()

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200

        result = collector._perform_check()

    assert result is True


def test_check_failure():
    collector = create_collector()

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500

        result = collector._perform_check()

    assert result is False


def test_check_exception_is_failure():
    collector = create_collector()

    with patch("requests.get", side_effect=RequestException()):
        result = collector._perform_check()

    assert result is False


# -----------------------------
# Tests: failure recording
# -----------------------------
def test_record_failure_adds_timestamp():
    collector = create_collector()

    assert len(collector.failures) == 0

    collector._record_failure()

    assert len(collector.failures) == 1


def test_cleanup_old_failures_removes_expired():
    collector = create_collector(alerting_window=10) # 10 pings * 10s = 100s window

    now = time.time()
    collector.failures.append(now - 110)  # expired
    collector.failures.append(now - 50)   # valid

    collector._cleanup_old_failures(now)

    assert len(collector.failures) == 1


# -----------------------------
# Tests: incident triggering
# -----------------------------
def test_should_trigger_incident_false_when_below_threshold():
    collector = create_collector(failure_threshold=3)

    collector.failures.extend([1, 2])

    assert collector._should_trigger_incident() is False


def test_should_trigger_incident_true_when_threshold_reached():
    collector = create_collector(failure_threshold=2)

    collector.failures.extend([1, 2])

    assert collector._should_trigger_incident() is True


# -----------------------------
# Tests: incident publishing
# -----------------------------
def test_publish_incident_creates_job():
    collector = create_collector()

    publisher = collector.queue_publisher

    collector._publish_incident()

    assert len(publisher.jobs) == 1

    job = publisher.jobs[0]
    assert job["type"] == "CREATE_INCIDENT"
    assert job["service_id"] == "1.1.1.1"
    assert job["status"] == "registered"
    assert "started_at" in job


# -----------------------------
# Tests: run_once behavior
# -----------------------------
def test_run_once_success_does_not_record_failure():
    collector = create_collector()

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        collector.run_once()

    assert len(collector.failures) == 0
    assert collector.queue_publisher.jobs == []


def test_run_once_failure_records_failure():
    collector = create_collector()

    with patch("requests.get", side_effect=ConnectionError()):
        collector.run_once()

    assert len(collector.failures) == 1


def test_run_once_triggers_incident_after_threshold():
    collector = create_collector(failure_threshold=2)

    with patch("requests.get", side_effect=ConnectTimeout()):
        collector.run_once()
        collector.run_once()

    publisher = collector.queue_publisher
    assert len(publisher.jobs) == 1


def test_run_once_does_not_trigger_incident_below_threshold():
    collector = create_collector(failure_threshold=3)

    with patch("requests.get", side_effect=ReadTimeout()):
        collector.run_once()
        collector.run_once()

    publisher = collector.queue_publisher
    assert publisher.jobs == []
