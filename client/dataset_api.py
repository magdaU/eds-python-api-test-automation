from typing import Any

import requests
from pydantic import BaseModel

from client.eds_client import EDSApiClient
from client.parsers import parse_records


class DatasetApi[ModelT: BaseModel]:
    """API object for one EDS dataset: knows its URL, hides the transport.

    `get` returns the raw response. With a `model`, `records` returns the records of a page as typed objects.
    """

    def __init__(self, client: EDSApiClient, dataset: str, model: type[ModelT] | None = None):
        self.client = client
        self.dataset = dataset
        self.model = model

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

    def records(
        self,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[ModelT]:
        """The records of one page as `model` objects. Raises `HTTPError` for an error status and
        `pydantic.ValidationError` when a record does not fit the model."""
        if self.model is None:
            raise TypeError(f"{self.dataset} has no model; create the DatasetApi with model=...")
        response = self.get(limit=limit, offset=offset, sort=sort, filters=filters)
        response.raise_for_status()
        return parse_records(response.json(), self.model)
