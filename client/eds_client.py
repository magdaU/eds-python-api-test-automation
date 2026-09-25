import logging
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.energidataservice.dk"
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.0
DEFAULT_BACKOFF_JITTER = 0.0
RETRYABLE_STATUS_CODES = [429, 500, 502, 503, 504]
SANE_MAX_RETRIES = 10
logger = logging.getLogger(__name__)


class EDSApiClient:
    """Thin wrapper around the Energi Data Service dataset API.

    Requests are retried with exponential backoff on rate limiting (429)
    and transient server errors. Tune `max_retries`/`backoff_factor`/
    `backoff_jitter` per instance, or per dataset via `dataset_overrides`,
    e.g. to back off harder against a dataset that hits rate limits more.
    """

    def __init__(
            self,
            base_url: str = BASE_URL,
            max_retries: int = DEFAULT_MAX_RETRIES,
            backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
            backoff_jitter: float = DEFAULT_BACKOFF_JITTER,
            dataset_overrides: dict | None = None,
    ):
        self.base_url = base_url
        self.session = requests.Session()

        default_adapter = self._build_adapter(max_retries, backoff_factor, backoff_jitter)
        self.session.mount("https://", default_adapter)
        self.session.mount("http://", default_adapter)

        for dataset, overrides in (dataset_overrides or {}).items():
            override_adapter = self._build_adapter(
                overrides.get("max_retries", max_retries),
                overrides.get("backoff_factor", backoff_factor),
                overrides.get("backoff_jitter", backoff_jitter),
            )
            self.session.mount(f"{base_url}/dataset/{dataset}", override_adapter)

    @staticmethod
    def _build_adapter(max_retries: int, backoff_factor: float, backoff_jitter: float) -> HTTPAdapter:
        if max_retries > SANE_MAX_RETRIES:
            logger.warning(
                "max_retries=%s exceeds the recommended maximum of %s -- this risks "
                "hammering the public EDS API during an outage or rate limit",
                max_retries, SANE_MAX_RETRIES,
            )

        retry = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            backoff_jitter=backoff_jitter,
            status_forcelist=RETRYABLE_STATUS_CODES,
            allowed_methods=["GET"],
        )
        return HTTPAdapter(max_retries=retry)

    @staticmethod
    def _encode_filter(filter: dict) -> str:
        pairs = ",".join(f'"{key}":"{value}"' for key, value in filter.items())
        return f"{{{pairs}}}"

    def get_dataset(self, dataset: str, limit: int = None, filter: dict = None, offset: int = None, sort: str = None) -> requests.Response:
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort is not None:
            params["sort"] = sort
        if filter is not None:
            params["filter"] = self._encode_filter(filter)
        url = f"{self.base_url}/dataset/{dataset}"
        logger.debug("GET %s params=%s", url, params)

        response = self.session.get(url, params=params)

        if response.status_code in RETRYABLE_STATUS_CODES:
            logger.warning("Received retryable status %s from %s", response.status_code, url)

        return response
