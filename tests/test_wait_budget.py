import pytest

from client.eds_client import EDSApiClient, RetryConfig
from client.retry import RetryAfterTooLong, RetryAfterTooLongError, WaitBudget
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "Wait budget", "critical")


def _client(server, waits, **options):
    retry = RetryConfig(max_retries=2, backoff_factor=0)
    return EDSApiClient(base_url=server.url, retry=retry, sleep=waits.append, **options)


def test_givenNoWaitBudget_whenServerThrottlesRepeatedly_thenEveryWaitIsTaken(scripted_server):
    # arrange
    server = scripted_server(429, 429, 200, headers={"Retry-After": "30"})
    waits = []

    # act
    response = _client(server, waits).get_dataset("CO2Emis", limit=1)

    # assert
    assert response.status_code == 200
    assert waits == [30, 30]


def test_givenWaitBudgetCoveringAllWaits_whenServerThrottlesTwice_thenRequestSucceeds(
    scripted_server,
):
    # arrange
    server = scripted_server(429, 429, 200, headers={"Retry-After": "30"})
    waits = []

    # act
    response = _client(server, waits, wait_budget=60).get_dataset("CO2Emis", limit=1)

    # assert
    assert response.status_code == 200
    assert waits == [30, 30]


def test_givenWaitBudgetExceeded_whenServerThrottlesAgain_thenRetryAfterTooLongErrorIsRaised(
    scripted_server,
):
    # arrange
    server = scripted_server(429, 429, 200, headers={"Retry-After": "30"})
    waits = []
    client = _client(server, waits, wait_budget=40)

    # act
    with pytest.raises(RetryAfterTooLongError) as error:
        client.get_dataset("CO2Emis", limit=1)

    # assert
    assert waits == [30]
    assert error.value.requested_seconds == 30
    assert error.value.allowed_seconds == 10


def test_givenBudgetSpentByFirstRequest_whenSecondRequestIsThrottled_thenBudgetIsShared(
    scripted_server,
):
    # arrange
    server = scripted_server(429, 200, 429, 200, headers={"Retry-After": "30"})
    waits = []
    client = _client(server, waits, wait_budget=40)
    client.get_dataset("CO2Emis", limit=1)

    # act
    with pytest.raises(RetryAfterTooLongError):
        client.get_dataset("CO2Emis", limit=1)

    # assert
    assert waits == [30]


def test_givenNegativeWaitBudget_whenCreatingClient_thenValueErrorNamesWaitBudget():
    # act
    with pytest.raises(ValueError, match="wait_budget") as error:
        EDSApiClient(wait_budget=-1)

    # assert
    assert str(error.value) == "wait_budget must not be negative, got -1"


def test_givenWaitWithinRemainingBudget_whenSleeping_thenWaitIsTakenAndCounted():
    # arrange
    waits = []
    budget = WaitBudget(120, wait=waits.append)

    # act
    budget.sleep(47)

    # assert
    assert waits == [47]
    assert budget.spent == 47


def test_givenWaitsThatAddUpToTheBudget_whenSleeping_thenAllAreTaken():
    # arrange
    waits = []
    budget = WaitBudget(120, wait=waits.append)

    # act
    budget.sleep(60)
    budget.sleep(60)

    # assert
    assert waits == [60, 60]
    assert budget.spent == 120


def test_givenWaitBeyondRemainingBudget_whenSleeping_thenRetryAfterTooLongIsRaisedWithoutWaiting():
    # arrange
    waits = []
    budget = WaitBudget(120, wait=waits.append)
    budget.sleep(100)

    # act
    with pytest.raises(RetryAfterTooLong) as error:
        budget.sleep(47)

    # assert
    assert waits == [100]
    assert error.value.requested_seconds == 47
    assert error.value.allowed_seconds == 20
