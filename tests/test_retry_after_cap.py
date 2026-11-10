import time
from email.utils import formatdate

import pytest

from client.eds_client import DEFAULT_MAX_RETRY_AFTER, RetryConfig
from client.retry import RetryAfterTooLongError
from tests.support.allure_labels import labels
from tests.support.scripted_server import api_for

pytestmark = labels("Client library", "Retry-After limit", "critical")


@pytest.fixture
def waits():
    """The seconds the retry logic asked to sleep; pass `waits.append` as `sleep=` to avoid really
    sleeping."""
    return []


def test_whenCreatingRetryConfig_thenTheDefaultLimitIsSixtySeconds():
    # act
    config = RetryConfig()

    # assert
    assert config.max_retry_after == DEFAULT_MAX_RETRY_AFTER == 60


def test_givenRetryAfterAboveTheLimit_whenServerThrottles_thenClientFailsFastWithoutWaiting(
    scripted_server, waits
):
    # arrange
    server = scripted_server(429, 200, headers={"Retry-After": "300"})

    # act
    with pytest.raises(RetryAfterTooLongError) as error:
        api_for(server, sleep=waits.append).get()

    # assert
    assert waits == []
    assert server.request_count == 1
    assert error.value.requested_seconds == 300
    assert error.value.allowed_seconds == DEFAULT_MAX_RETRY_AFTER


def test_givenRetryAfterAtTheLimit_whenServerThrottles_thenClientWaitsAndSucceeds(
    scripted_server, waits
):
    # arrange
    server = scripted_server(429, 200, headers={"Retry-After": str(int(DEFAULT_MAX_RETRY_AFTER))})

    # act
    response = api_for(server, sleep=waits.append).get()

    # assert
    assert waits == [DEFAULT_MAX_RETRY_AFTER]
    assert response.status_code == 200


def http_date(seconds_from_now):
    return formatdate(time.time() + seconds_from_now, usegmt=True)
