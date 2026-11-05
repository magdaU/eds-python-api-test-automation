import time
from email.utils import formatdate

import pytest

from client.eds_client import EDSApiClient, RetryConfig
from client.retry import RetryAfterTooLongError
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


def test_givenRetryAfterZeroAsTheOnlyFailure_whenServerThenAcceptsRetry_thenZeroWaitIsHonoured(
    scripted_server,
):
    # arrange
    server = scripted_server(429, 200, headers=[{"Retry-After": "0"}, {}])
    client, waits = client_recording_waits(server)

    # act
    response = client.get_dataset("CO2Emis")

    # assert
    assert response.status_code == 200
    assert waits == [0.0]


def test_givenRetryAfterOneSecond_whenServerThenAcceptsRetry_thenOneSecondIsWaited(scripted_server):
    # arrange
    server = scripted_server(429, 200, headers={"Retry-After": "1"})
    client, waits = client_recording_waits(server)

    # act
    response = client.get_dataset("CO2Emis")

    # assert
    assert response.status_code == 200
    assert waits == [1.0]


def test_givenRetryAfterHttpDate_whenServerThenAcceptsRetry_thenWaitIsAboutFiveSeconds(
    scripted_server,
):
    # arrange
    http_date = formatdate(time.time() + 5, usegmt=True)
    server = scripted_server(429, 200, headers={"Retry-After": http_date})
    client, waits = client_recording_waits(server)

    # act
    response = client.get_dataset("CO2Emis")

    # assert
    assert response.status_code == 200
    assert len(waits) == 1
    assert 3 <= waits[0] <= 5


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


def test_givenNegativeRetryAfterAfter503_whenServerThenAcceptsRetry_thenBackoffIsUsed(
    scripted_server,
):
    # arrange
    server = scripted_server(503, 429, 200, headers=[{}, {"Retry-After": "-5"}, {}])
    client, waits = client_recording_waits(server)

    # act
    response = client.get_dataset("CO2Emis")

    # assert
    assert response.status_code == 200
    assert waits == [2.0]


def test_givenRetryAfterAboveTheMaximum_whenServerThrottles_thenClientRefusesWithoutWaiting(
    scripted_server,
):
    # arrange
    server = scripted_server(429, 200, headers={"Retry-After": "100000"})
    client, waits = client_recording_waits(server)

    # act
    with pytest.raises(RetryAfterTooLongError):
        client.get_dataset("CO2Emis")

    # assert
    assert waits == []


def test_givenNoRetryAfterHeader_whenServerFailsThreeTimes_thenBackoffGrowsExponentially(
    scripted_server,
):
    # arrange
    server = scripted_server(503, 503, 503, 200)
    client, waits = client_recording_waits(server)

    # act
    response = client.get_dataset("CO2Emis")

    # assert
    assert response.status_code == 200
    assert waits == [2.0, 4.0]
