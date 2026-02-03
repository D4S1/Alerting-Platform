import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

from monitoring_module.collector import IPStatusCollector


@pytest.fixture
def service():
    return {
        "id": 1,
        "IP": "1.1.1.1",
        "frequency_seconds": 10,
        "alerting_window_npings": 10,
        "failure_threshold": 3
    }


@pytest.fixture
def collector(service):
    fake_publisher = AsyncMock()
    fake_publisher.publish.return_value = "ok"

    return IPStatusCollector(
        service=service,
        api_base_url="http://api",
        pubsub_topic="projects/test/topics/incidents",
        publisher=fake_publisher
    )


# -------------------- _perform_check --------------------

@pytest.mark.asyncio
async def test_check_success(collector):
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        assert await collector._perform_check() is True


@pytest.mark.asyncio
async def test_check_failure_status(collector):
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 500
        assert await collector._perform_check() is False


@pytest.mark.asyncio
async def test_check_exception(collector):
    with patch("httpx.AsyncClient.get", side_effect=httpx.RequestError("Error")):
        assert await collector._perform_check() is False


# -------------------- Failure logic --------------------

@pytest.mark.asyncio
async def test_record_failure_calls_api(collector):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        await collector._record_failure()
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_should_trigger_incident_false(collector):
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json.return_value = [1]  # 1 failure < threshold
        assert await collector._should_trigger_incident() is False


@pytest.mark.asyncio
async def test_should_trigger_incident_true(collector):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [1, 2, 3]

    # Mock auth
    with patch("monitoring_module.collector.get_headers_async", return_value={"Authorization": "Bearer test"}):
        
        # Mock httpx.AsyncClient.get as ASYNC mock
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            assert await collector._should_trigger_incident() is True

# -------------------- Incident flow --------------------

@pytest.mark.asyncio
async def test_run_once_creates_incident_and_publishes(collector):
    with patch.object(collector, "_perform_check", return_value=False), \
         patch.object(collector, "_record_failure", new_callable=AsyncMock), \
         patch.object(collector, "_should_trigger_incident", return_value=True), \
         patch.object(collector, "_get_open_incident", return_value=None), \
         patch.object(collector, "_create_incident", return_value={"id": 123}), \
         patch.object(collector, "_publish_incident", new_callable=AsyncMock) as mock_pub:

        await collector.run_once()
        mock_pub.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_run_once_resolves_incident_when_recovered(collector):
    with patch.object(collector, "_perform_check", return_value=True), \
         patch.object(collector, "_should_trigger_incident", return_value=False), \
         patch.object(collector, "_get_open_incident", return_value={"id": 55}), \
         patch.object(collector, "_resolve_incident", new_callable=AsyncMock) as mock_resolve:

        await collector.run_once()
        mock_resolve.assert_called_once_with(55)


@pytest.mark.asyncio
async def test_run_once_no_duplicate_incident(collector):
    with patch.object(collector, "_perform_check", return_value=False), \
         patch.object(collector, "_record_failure", new_callable=AsyncMock), \
         patch.object(collector, "_should_trigger_incident", return_value=True), \
         patch.object(collector, "_get_open_incident", return_value={"id": 9}), \
         patch.object(collector, "_create_incident", new_callable=AsyncMock) as mock_create:

        await collector.run_once()
        mock_create.assert_not_called()
