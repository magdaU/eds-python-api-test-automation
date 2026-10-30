import time
from email.utils import formatdate

import pytest
import requests

from client.eds_client import DEFAULT_MAX_RETRY_AFTER, RetryConfig
from client.retry import RetryAfterTooLongError
from tests.support.allure_labels import labels
from tests.support.scripted_server import api_for

pytestmark = labels("Client library", "Retry-After limit", "critical")


@pytest.fixture
def waits(monkeypatch):
    """The seconds the retry logic asked to sleep, without really sleeping."""
    recorded = []
    monkeypatch.setattr("urllib3.util.retry.time.sleep", recorded.append)
    return recorded


def test_whenCreatingRetryConfig_thenTheDefaultLimitIsSixtySeconds():
    # act
    config = RetryConfig()

    # assert
    assert config.max_retry_after == DEFAULT_MAX_RETRY_AFTER == 60


def test_whenCheckingTheErrorType_thenItIsASubclassOfRetryError():
    # act / assert
    assert issubclass(RetryAfterTooLongError, requests.exceptions.RetryError)


def test_givenRetryAfterAboveTheLimit_whenServerThrottles_thenClientFailsFastWithoutWaiting(scripted_server, waits):
    # arrange
    server = scripted_server(429, 200, headers={"Retry-After": "300"})

    # act
    with pytest.raises(RetryAfterTooLongError) as error:
        api_for(server).get()

    # assert
    assert waits == []
    assert server.request_count == 1
    assert "300 s" in str(error.value)
    assert "60 s" in str(error.value)


@pytest.mark.parametrize(("seconds", "gives_up"), [(60, False), (61, True)], ids=["at-the-limit", "just-above-the-limit"])
def test_givenRetryAfterAroundTheLimit_whenServerThrottles_thenOnlyAboveTheLimitIsRefused(
    scripted_server, waits, seconds, gives_up
):
    # arrange
    server = scripted_server(429, 200, headers={"Retry-After": str(seconds)})
    api = api_for(server)

    # act
    if gives_up:
        with pytest.raises(RetryAfterTooLongError):
            api.get()
    else:
        response = api.get()

    # assert
    assert waits == ([] if gives_up else [seconds])
    assert gives_up or response.status_code == 200


def http_date(seconds_from_now):
    return formatdate(time.time() + seconds_from_now, usegmt=True)


def test_givenRetryAfterAsHttpDateAboveTheLimit_whenServerThrottles_thenClientFailsFastWithoutWaiting(scripted_server, waits):
    # arrange
    server = scripted_server(429, 200, headers={"Retry-After": http_date(300)})

    # act
    with pytest.raises(RetryAfterTooLongError):
        api_for(server).get()

    # assert
    assert waits == []
    assert server.request_count == 1


def test_givenRetryAfterAsHttpDateBelowTheLimit_whenServerThrottles_thenClientWaitsUntilThatTime(scripted_server, waits):
    # arrange
    server = scripted_server(429, 200, headers={"Retry-After": http_date(30)})

    # act
    response = api_for(server).get()

    # assert
    assert response.status_code == 200
    assert len(waits) == 1
    assert 25 <= waits[0] <= 30


def test_givenNoLimit_whenServerAsksForALongWait_thenClientStillWaits(scripted_server, waits):
    # arrange
    server = scripted_server(429, 200, headers={"Retry-After": "300"})

    # act
    response = api_for(server, max_retry_after=None).get()

    # assert
    assert waits == [300]
    assert response.status_code == 200


def test_givenAnAllowedWait_whenTheNextWaitIsTooLong_thenClientGivesUpAtTheSecondOne(scripted_server, waits):
    # arrange
    server = scripted_server(429, 429, 200, headers=[{"Retry-After": "2"}, {"Retry-After": "300"}, {}])

    # act
    with pytest.raises(RetryAfterTooLongError):
        api_for(server).get()

    # assert
    assert waits == [2]
    assert server.request_count == 2
