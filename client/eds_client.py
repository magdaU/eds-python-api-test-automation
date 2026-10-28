import json
import logging
from dataclasses import dataclass
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.energidataservice.dk"
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.0
DEFAULT_BACKOFF_JITTER = 0.0
DEFAULT_TIMEOUT = 10
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
SANE_MAX_RETRIES = 10
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetryConfig:
    """Retry/backoff settings. A misspelled setting raises `TypeError` instead of being ignored."""

    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    backoff_jitter: float = DEFAULT_BACKOFF_JITTER


DEFAULT_RETRY = RetryConfig()


class EDSApiClient:
    """Thin wrapper around the Energi Data Service dataset API.

    Requests are retried with exponential backoff on rate limiting (429)
    and transient server errors. Tune the `retry` settings per instance, or per
    dataset via `dataset_overrides`, e.g. to back off harder against a dataset that
    hits rate limits more. An override replaces the instance settings as a whole.
    `timeout` (seconds) applies to each connect/read of a single attempt, not
    to the whole retry cycle, so a server-ordered `Retry-After` wait is not cut short.
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        retry: RetryConfig = DEFAULT_RETRY,
        dataset_overrides: dict[str, RetryConfig] | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        self._mount_retry("https://", retry)
        self._mount_retry("http://", retry)
        for dataset, override in (dataset_overrides or {}).items():
            self._mount_retry(self.dataset_url(dataset), override)

    def _mount_retry(self, url_prefix: str, config: RetryConfig) -> None:
        self.session.mount(url_prefix, self._build_adapter(config))

    @staticmethod
    def _build_adapter(config: RetryConfig) -> HTTPAdapter:
        if config.max_retries > SANE_MAX_RETRIES:
            logger.warning(
                "max_retries=%s exceeds the recommended maximum of %s -- this risks "
                "hammering the public EDS API during an outage or rate limit",
                config.max_retries,
                SANE_MAX_RETRIES,
            )

        retry = Retry(
            total=config.max_retries,
            backoff_factor=config.backoff_factor,
            backoff_jitter=config.backoff_jitter,
            status_forcelist=RETRYABLE_STATUS_CODES,
            allowed_methods=["GET"],
        )
        return HTTPAdapter(max_retries=retry)

    @staticmethod
    def _encode_filters(filters: dict[str, Any]) -> str:
        return json.dumps(filters, separators=(",", ":"))

    def get_dataset(
        self,
        dataset: str,
        limit: int | None = None,
        filters: dict[str, Any] | None = None,
        offset: int | None = None,
        sort: str | None = None,
    ) -> requests.Response:
        """`limit=0` returns every record; a negative `limit` is rejected because the API
        treats it the same way (it returned a 2-million-record dataset in one response)."""
        if limit is not None and limit < 0:
            raise ValueError(f"limit must not be negative, got {limit}")
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort is not None:
            params["sort"] = sort
        if filters is not None:
            params["filter"] = self._encode_filters(filters)
        return self._get(self.dataset_url(dataset), params)

    def get_news(self, path: str = "", params: dict[str, Any] | None = None) -> requests.Response:
        """GET /News, or a sub-resource: "actual", "calendar" or "archived"."""
        return self._get(self.news_url(path), params or {})

    def dataset_url(self, dataset: str) -> str:
        return f"{self.base_url}/dataset/{dataset}"

    def news_url(self, path: str = "") -> str:
        return "/".join(part for part in (f"{self.base_url}/News", path.strip("/")) if part)

    def _get(self, url: str, params: dict[str, Any]) -> requests.Response:
        logger.debug("GET %s params=%s", url, params)

        try:
            return self.session.get(url, params=params, timeout=self.timeout)
        except requests.exceptions.RetryError as error:
            # Retryable statuses never reach the caller as a response: urllib3 retries them and,
            # once the budget is spent, raises. This is where that would otherwise go unnoticed.
            logger.warning("Giving up on %s after retries: %s", url, error)
            raise
