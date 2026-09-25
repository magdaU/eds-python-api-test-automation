import logging
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.energidataservice.dk"
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.0
RETRYABLE_STATUS_CODES = [429, 500, 502, 503, 504]
logger = logging.getLogger(__name__)


class EDSApiClient:
    """Thin wrapper around the Energi Data Service dataset API.

    Requests are retried with exponential backoff on rate limiting (429)
    and transient server errors. Tune `max_retries`/`backoff_factor` per
    instance, e.g. to back off harder against the API's rate limits.
    """

    def __init__(
            self,
            base_url: str = BASE_URL,
            max_retries: int = DEFAULT_MAX_RETRIES,
            backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ):
        self.base_url = base_url
        self.session = requests.Session()

        retry = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=RETRYABLE_STATUS_CODES,
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

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
