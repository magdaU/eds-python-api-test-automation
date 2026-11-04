import pytest

from client.eds_client import EDSApiClient

# Only network errors are rerun. A `RetryError` means the API throttled or failed us: rerunning
# after 5 s would add load to an API that has just asked us to slow down.
TRANSIENT_NETWORK_ERRORS = ["ConnectionError", "Timeout"]

# Seconds of waiting (Retry-After and backoff) that all live tests of one run may spend together.
# Once it is used up, the next wait is refused and the test that needed it is skipped, not failed.
LIVE_RETRY_BUDGET_SECONDS = 120


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
    in `tests/conftest.py`. The client keeps its default retry settings and gets the run's
    `wait_budget`. Offline tests keep the plain default client."""
    with EDSApiClient(wait_budget=LIVE_RETRY_BUDGET_SECONDS) as client:
        yield client
