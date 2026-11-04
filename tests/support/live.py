import time
from collections.abc import Callable

import pytest

from client.eds_client import EDSApiClient
from client.retry import RetryAfterTooLong

# Only network errors are rerun. A `RetryError` means the API throttled or failed us: rerunning
# after 5 s would add load to an API that has just asked us to slow down.
TRANSIENT_NETWORK_ERRORS = ["ConnectionError", "Timeout"]

# Seconds of waiting (Retry-After and backoff) that all live tests of one run may spend together.
# Once it is used up, the next wait is refused and the test that needed it is skipped, not failed.
LIVE_RETRY_BUDGET_SECONDS = 120


class RetryBudget:
    """Shared by every live test of one run: a wait that would exceed the budget is refused.

    The refusal is a `RetryAfterTooLong`, which the client turns into `RetryAfterTooLongError`;
    `tests/conftest.py` reports that as a skipped test. The client itself has no budget.
    """

    def __init__(self, seconds: float, wait: Callable[[float], None] = time.sleep) -> None:
        self.seconds = seconds
        self.spent = 0.0
        self.wait = wait

    def sleep(self, seconds: float) -> None:
        remaining = self.seconds - self.spent
        if seconds > remaining:
            raise RetryAfterTooLong(
                f"the live retry budget of {self.seconds:.0f} s for this run is used up "
                f"({self.spent:.0f} s spent); the next wait of {seconds:.0f} s is not taken",
                requested_seconds=seconds,
                allowed_seconds=remaining,
            )
        self.spent += seconds
        self.wait(seconds)


LIVE_RETRY_BUDGET = RetryBudget(LIVE_RETRY_BUDGET_SECONDS)

# Measured on 2026-10-28 for Elspotprices (since discontinued): the EDS API answered one query per
# window of about 300 s
# (per client). A different query, or the same one after its ~44 s cache lifetime, got 429 with
# `Retry-After` for the rest
# of the window (the repeat at +14 s took 36 ms from cache, the one at +89 s got 429). CO2Emis has
# no such limit.
# The limit of DayAheadPrices is not measured, so a test run still sends exactly one query to it,
# shared by every live test
# that needs its data (`dayaheadprices_latest`). Two runs less than five minutes apart could
# collide; the client then
# fails fast (RetryAfterTooLongError) instead of waiting.
DAYAHEADPRICES_LIVE_QUERY = {"limit": 5, "sort": "DayAheadPriceDKK desc"}


@pytest.fixture(name="eds_client", scope="session")
def live_eds_client():
    """Named `eds_client`: a live module that imports it overrides the offline fixture of that name
    in `tests/conftest.py`. The client keeps its default retry settings; only its waits are counted
    against `LIVE_RETRY_BUDGET`. Offline tests keep the plain default client."""
    with EDSApiClient(sleep=LIVE_RETRY_BUDGET.sleep) as client:
        yield client
