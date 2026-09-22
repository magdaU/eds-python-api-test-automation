import requests

BASE_URL = "https://api.energidataservice.dk"


class EDSApiClient:
    """Thin wrapper around the Energi Data Service dataset API."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    def get_dataset(self, dataset: str, limit: int = None, filter: dict = None) -> requests.Response:
        params = {}
        if limit is not None:
            params["limit"] = limit
        if filter is not None:
            params["filter"] = self._encode_filter(filter)

        return requests.get(f"{self.base_url}/dataset/{dataset}", params=params)

    @staticmethod
    def _encode_filter(filter: dict) -> str:
        pairs = ",".join(f'"{key}":"{value}"' for key, value in filter.items())
        return f"{{{pairs}}}"
