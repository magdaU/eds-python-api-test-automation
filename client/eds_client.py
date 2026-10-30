import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Self
from urllib.parse import quote

import requests
from requests.adapters import BaseAdapter, HTTPAdapter

from client.retry import LoggingRetry, RetryAfterTooLong, RetryAfterTooLongError

BASE_URL = "https://api.energidataservice.dk"
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.0
DEFAULT_BACKOFF_JITTER = 0.0
# seconds; the API has asked for 4-7 s routinely and for 217-300 s when it throttled a run
DEFAULT_MAX_RETRY_AFTER = 60.0
DEFAULT_TIMEOUT = 10
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
SANE_MAX_RETRIES = 10
ERROR_BODY_PREVIEW_CHARS = 300
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetryConfig:
    """Retry/backoff settings. A misspelled setting raises `TypeError` instead of being ignored."""

    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    backoff_jitter: float = DEFAULT_BACKOFF_JITTER
    max_retry_after: float | None = DEFAULT_MAX_RETRY_AFTER


DEFAULT_RETRY = RetryConfig()


class _Session(requests.Session):
    """A `Session` that gives a dataset its own retry adapter, and only that dataset.

    `Session.mount` matches a URL by prefix, so an adapter mounted for `/dataset/CO2Emis` would also serve
    `/dataset/CO2EmisProg`. Here the URL has to be the dataset's own, with or without a query string.
    """

    def __init__(self) -> None:
        super().__init__()
        self.dataset_adapters: dict[str, HTTPAdapter] = {}

    def get_adapter(self, url: str) -> BaseAdapter:
        return self.dataset_adapters.get(url.split("?", 1)[0]) or super().get_adapter(url)

    def close(self) -> None:
        super().close()
        for adapter in self.dataset_adapters.values():
            adapter.close()


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
        self.session = _Session()

        self._mount_retry("https://", retry)
        self._mount_retry("http://", retry)
        for dataset, override in (dataset_overrides or {}).items():
            self.session.dataset_adapters[self.dataset_url(dataset)] = self._build_adapter(override)

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

        retry = LoggingRetry(
            total=config.max_retries,
            backoff_factor=config.backoff_factor,
            backoff_jitter=config.backoff_jitter,
            max_retry_after=config.max_retry_after,
            status_forcelist=RETRYABLE_STATUS_CODES,
            allowed_methods=["GET"],
        )
        return HTTPAdapter(max_retries=retry)

    @staticmethod
    def _encode_filters(filters: dict[str, Any]) -> str:
        return json.dumps(filters, separators=(",", ":"))

    def close(self) -> None:
        """Release the pooled connections of the session. The client is also a context manager."""
        self.session.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def get_dataset(
        self,
        dataset: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> requests.Response:
        """`limit=0` returns every record; a negative `limit` is rejected because the API
        treats it the same way (it returned a 2-million-record dataset in one response).
        The query arguments are keyword-only, in the same order as `DatasetApi.get`."""
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

    def get_dataset_metadata(self, dataset: str) -> requests.Response:
        """GET /meta/dataset/<name>: title, update frequency and whether EDS still publishes the dataset."""
        return self._get(f"{self.base_url}/meta/dataset/{_path_segment(dataset)}", {})

    def get_news(self, path: str = "", params: dict[str, Any] | None = None) -> requests.Response:
        """GET /News, or a sub-resource: "actual", "calendar" or "archived"."""
        return self._get(self.news_url(path), params or {})

    def dataset_url(self, dataset: str) -> str:
        return f"{self.base_url}/dataset/{_path_segment(dataset)}"

    def news_url(self, path: str = "") -> str:
        return "/".join(part for part in (f"{self.base_url}/News", path.strip("/")) if part)

    def _get(self, url: str, params: dict[str, Any]) -> requests.Response:
        started = time.perf_counter()
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except RetryAfterTooLong as error:
            logger.warning("Giving up on %s: %s", url, error)
            raise RetryAfterTooLongError(str(error)) from error
        except requests.exceptions.RetryError as error:
            # Retryable statuses never reach the caller as a response: urllib3 retries them and,
            # once the budget is spent, raises. This is where that would otherwise go unnoticed.
            logger.warning("Giving up on %s after retries, %.0f ms: %s", url, _milliseconds_since(started), error)
            raise
        self._log_response(url, params, response, started)
        return response

    @staticmethod
    def _log_response(url: str, params: dict[str, Any], response: requests.Response, started: float) -> None:
        """One line per request: what was asked, the status and how long it took (waits for retries included).

        An error response also gets the start of its body, which is where the API says what was wrong.
        """
        line = f"GET {url} params={params} -> {response.status_code} in {_milliseconds_since(started):.0f} ms"
        if response.ok:
            logger.info(line)
        else:
            logger.info("%s body=%s", line, response.text[:ERROR_BODY_PREVIEW_CHARS])


def _milliseconds_since(started: float) -> float:
    return (time.perf_counter() - started) * 1000


def _path_segment(value: str) -> str:
    """Encode `value` as one URL path segment, so a `/`, `?` or `#` in it cannot change what is requested."""
    return quote(value, safe="")
