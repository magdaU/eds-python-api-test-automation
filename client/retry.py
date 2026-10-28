import logging

from urllib3 import BaseHTTPResponse
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class LoggingRetry(Retry):
    """`Retry` that logs how long it is about to wait and why; that wait is otherwise invisible.

    A server-ordered `Retry-After` can be minutes long and is spent inside the HTTP stack, so without this a slow run
    looks like a hang.
    """

    def sleep(self, response: BaseHTTPResponse | None = None) -> None:
        retry_after = self.get_retry_after(response) if response else None
        reason = f"status {response.status}" if response else "no response"
        if retry_after:
            logger.warning("Retrying in %.1f s because the server sent Retry-After (%s)", retry_after, reason)
        else:
            logger.warning("Retrying in %.1f s, backoff (%s)", self.get_backoff_time(), reason)
        super().sleep(response)
