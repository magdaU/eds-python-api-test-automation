from client.eds_client import EDSApiClient, RetryConfig
from tests.support.allure_labels import labels

# These tests use a real local HTTP server (`scripted_server`), not requests_mock: requests_mock
# replaces the transport and skips urllib3's Retry, so it would never exercise the retry logic.
pytestmark = labels("Client library", "Retry-After header", "critical")

BACKOFF_FACTOR = 1.0


def client_recording_waits(server):
    """A client whose waits are recorded instead of slept, so the tests never really wait."""
    waits = []
    client = EDSApiClient(
        base_url=server.url,
        retry=RetryConfig(max_retries=3, backoff_factor=BACKOFF_FACTOR),
        sleep=waits.append,
    )
    return client, waits


def test_givenRetryAfterZeroAfter503_whenServerThenAcceptsRetry_thenZeroWaitIsHonoured(
    scripted_server,
):
    # arrange
    server = scripted_server(503, 429, 200, headers=[{}, {"Retry-After": "0"}, {}])
    client, waits = client_recording_waits(server)

    # act
    response = client.get_dataset("CO2Emis")

    # assert
    assert response.status_code == 200
    assert waits == [0.0]


def test_givenInvalidRetryAfterAfter503_whenServerThenAcceptsRetry_thenBackoffIsUsed(
    scripted_server,
):
    # arrange
    server = scripted_server(503, 429, 200, headers=[{}, {"Retry-After": "soon"}, {}])
    client, waits = client_recording_waits(server)

    # act
    response = client.get_dataset("CO2Emis")

    # assert
    assert response.status_code == 200
    assert waits == [2.0]
