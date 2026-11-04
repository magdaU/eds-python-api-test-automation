import pytest

from client.retry import RetryAfterTooLong
from tests.support.allure_labels import labels
from tests.support.live import RetryBudget

pytestmark = labels("Client library", "Live retry budget", "critical")


def test_givenWaitWithinBudget_whenSleeping_thenWaitIsTakenAndCounted():
    # arrange
    waits = []
    budget = RetryBudget(120, wait=waits.append)

    # act
    budget.sleep(47)

    # assert
    assert waits == [47]
    assert budget.spent == 47


def test_givenWaitsThatAddUpToTheBudget_whenSleeping_thenAllAreTaken():
    # arrange
    waits = []
    budget = RetryBudget(120, wait=waits.append)

    # act
    budget.sleep(60)
    budget.sleep(60)

    # assert
    assert waits == [60, 60]
    assert budget.spent == 120


def test_givenWaitBeyondRemainingBudget_whenSleeping_thenRetryAfterTooLongIsRaisedWithoutWaiting():
    # arrange
    waits = []
    budget = RetryBudget(120, wait=waits.append)
    budget.sleep(100)

    # act
    with pytest.raises(RetryAfterTooLong) as error:
        budget.sleep(47)

    # assert
    assert waits == [100]
    assert error.value.requested_seconds == 47
    assert error.value.allowed_seconds == 20
    assert "the live retry budget of 120 s for this run is used up" in str(error.value)
