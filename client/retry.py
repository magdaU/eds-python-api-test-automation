import logging
import time
from collections.abc import Callable
from typing import Any, Self

import requests
from urllib3 import BaseHTTPResponse
from urllib3.exceptions import InvalidHeader
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class RetryAfterTooLongError(requests.exceptions.RetryError):
    """The server asked for a longer wait than the client allows, so it gave up instead of
    waiting.

    `requested_seconds` is the wait the server asked for and `allowed_seconds` the limit it
    exceeded; both are `None` when the error is raised without them.
    """

    def __init__(
        self,
        message: str,
        *,
        requested_seconds: float | None = None,
        allowed_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.requested_seconds = requested_seconds
        self.allowed_seconds = allowed_seconds


class RetryAfterTooLong(Exception):
    """Raised inside the retry logic.

    Not an `OSError` on purpose: `requests` turns every `OSError` raised there into a
    `ConnectionError`, which would hide the reason. `EDSApiClient` converts it into
    `RetryAfterTooLongError`, keeping the seconds.
    """

    def __init__(self, message: str, *, requested_seconds: float, allowed_seconds: float) -> None:
        super().__init__(message)
        self.requested_seconds = requested_seconds
        self.allowed_seconds = allowed_seconds


class WaitBudget:
    """Total seconds of waiting (`Retry-After` and backoff) that one client may spend.

    A wait that would go over the budget is refused with `RetryAfterTooLong` and not taken; the
    client turns that into `RetryAfterTooLongError`. Every request of the client shares the budget.
    `wait` performs the waits that are taken (default `time.sleep`).
    """

    def __init__(self, seconds: float, wait: Callable[[float], None] = time.sleep) -> None:
        self.seconds = seconds
        self.spent = 0.0
        self.wait = wait

    def sleep(self, seconds: float) -> None:
        remaining = self.seconds - self.spent
        if seconds > remaining:
            raise RetryAfterTooLong(
                f"the wait budget of {self.seconds:.0f} s for this client is used up "
                f"({self.spent:.0f} s spent); the next wait of {seconds:.0f} s is not taken",
                requested_seconds=seconds,
                allowed_seconds=remaining,
            )
        self.spent += seconds
        self.wait(seconds)


class LoggingRetry(Retry):
    """`Retry` that logs how long it is about to wait and why, and refuses a `Retry-After` that
    is too long.

    A server-ordered `Retry-After` can be minutes long and is spent inside the HTTP stack, so
    without this a slow run looks like a hang. With `max_retry_after` set, a longer wait ends the
    request at once with `RetryAfterTooLongError`.

    Every wait goes through `sleep_func` (default `time.sleep`). A test passes its own function,
    which records the seconds instead of waiting. That is why tests do not patch `time.sleep`:
    urllib3 uses the global `time` module, so such a patch would replace `time.sleep` everywhere
    for as long as the test runs, test code included.
    """

    def __init__(
        self,
        *args: Any,
        max_retry_after: float | None = None,
        sleep_func: Callable[[float], None] = time.sleep,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.max_retry_after = max_retry_after
        self.sleep_func = sleep_func

    def new(self, **kw: Any) -> Self:
        """urllib3 builds a fresh `Retry` for every attempt; the limit and the sleep function have
        to survive that."""
        retry = super().new(**kw)
        retry.max_retry_after = self.max_retry_after
        retry.sleep_func = self.sleep_func
        return retry

    def get_retry_after(self, response: BaseHTTPResponse) -> float | None:
        """The seconds of a `Retry-After` header, or `None` when there is no usable one.

        `0` is a valid value (retry at once), so the caller must test for `None`, not for
        truthiness. An invalid header (not a number, not a date, or negative) is logged and
        ignored, so the request falls back to backoff instead of failing with `InvalidHeader`.
        """
        try:
            return super().get_retry_after(response)
        except InvalidHeader as error:
            logger.warning("Ignoring an invalid Retry-After header, using backoff: %s", error)
            return None

    def sleep(self, response: BaseHTTPResponse | None = None) -> None:
        retry_after = (
            self.get_retry_after(response) if response and self.respect_retry_after_header else None
        )
        reason = f"status {response.status}" if response else "no response"
        if (
            retry_after is not None
            and self.max_retry_after is not None
            and retry_after > self.max_retry_after
        ):
            raise RetryAfterTooLong(
                f"The server asked to wait {retry_after:.0f} s (Retry-After, {reason}), "
                f"more than the {self.max_retry_after:.0f} s allowed; not waiting",
                requested_seconds=retry_after,
                allowed_seconds=self.max_retry_after,
            )
        if retry_after is not None:
            logger.warning(
                "Retrying in %.1f s because the server sent Retry-After (%s)", retry_after, reason
            )
            self.sleep_func(retry_after)
            return
        # measured once: with jitter every call draws a new value, so a second call would wait a
        # different time than logged
        backoff = self.get_backoff_time()
        logger.warning("Retrying in %.1f s, backoff (%s)", backoff, reason)
        if backoff > 0:
            self.sleep_func(backoff)
