import logging
from typing import Any, Self

import requests
from urllib3 import BaseHTTPResponse
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class RetryAfterTooLongError(requests.exceptions.RetryError):
    """The server asked for a longer wait than the client allows, so it gave up instead of waiting."""


class RetryAfterTooLong(Exception):
    """Raised inside the retry logic. Not an `OSError` on purpose: `requests` turns every `OSError` raised there into a
    `ConnectionError`, which would hide the reason. `EDSApiClient` converts it into `RetryAfterTooLongError`."""


class LoggingRetry(Retry):
    """`Retry` that logs how long it is about to wait and why, and refuses a `Retry-After` that is too long.

    A server-ordered `Retry-After` can be minutes long and is spent inside the HTTP stack, so without this a slow run
    looks like a hang. With `max_retry_after` set, a longer wait ends the request at once with `RetryAfterTooLongError`.
    """

    def __init__(self, *args: Any, max_retry_after: float | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.max_retry_after = max_retry_after

    def new(self, **kw: Any) -> Self:
        """urllib3 builds a fresh `Retry` for every attempt; the limit has to survive that."""
        retry = super().new(**kw)
        retry.max_retry_after = self.max_retry_after
        return retry

    def sleep(self, response: BaseHTTPResponse | None = None) -> None:
        retry_after = self.get_retry_after(response) if response and self.respect_retry_after_header else None
        reason = f"status {response.status}" if response else "no response"
        if retry_after and self.max_retry_after is not None and retry_after > self.max_retry_after:
            raise RetryAfterTooLong(
                f"The server asked to wait {retry_after:.0f} s (Retry-After, {reason}), "
                f"more than the {self.max_retry_after:.0f} s allowed; not waiting"
            )
        if retry_after:
            logger.warning("Retrying in %.1f s because the server sent Retry-After (%s)", retry_after, reason)
        else:
            logger.warning("Retrying in %.1f s, backoff (%s)", self.get_backoff_time(), reason)
        super().sleep(response)
