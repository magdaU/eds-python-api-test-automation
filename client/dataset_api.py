from typing import Any

import requests

from client.eds_client import EDSApiClient


class DatasetApi:
    """API object for one EDS dataset: knows its URL, hides the transport."""

    def __init__(self, client: EDSApiClient, dataset: str):
        self.client = client
        self.dataset = dataset

    @property
    def url(self) -> str:
        return self.client.dataset_url(self.dataset)

    def metadata(self) -> requests.Response:
        return self.client.get_dataset_metadata(self.dataset)

    def get(
        self,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self.client.get_dataset(self.dataset, limit=limit, offset=offset, sort=sort, filters=filters)
