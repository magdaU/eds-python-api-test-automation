from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

from client.eds_client import EDSApiClient
from tests.support.mocks import records_response


@dataclass(frozen=True)
class SentRequest:
    """What the client sent: the path as sent (percent-encoding preserved), the query parameters
    with their original case, and the timeout of the attempt."""

    path: str
    query: dict[str, list[str]]
    timeout: float | None


class FakeEndpoint:
    """One URL of the fake EDS server; `answers` decides what the client gets back from it."""

    def __init__(self, mocker, url: str):
        self.mocker = mocker
        self.url = url

    def answers(
        self,
        records: Any = (),
        status: int = 200,
        json: Any = None,
        text: str | None = None,
    ) -> None:
        """Answer with `records` in the dataset envelope, or with `json` / `text` as given."""
        if text is not None:
            self.mocker.get(self.url, status_code=status, text=text)
            return
        body = json if json is not None else records_response(list(records))
        self.mocker.get(self.url, status_code=status, json=body)


class FakeEds:
    """The EDS API as a test double: register what an endpoint answers, then read what was sent."""

    def __init__(self, mocker, client: EDSApiClient):
        self.mocker = mocker
        self.client = client

    def dataset(self, name: str) -> FakeEndpoint:
        return FakeEndpoint(self.mocker, self.client.dataset_url(name))

    def metadata(self, name: str) -> FakeEndpoint:
        return FakeEndpoint(self.mocker, f"{self.client.base_url}/meta/dataset/{name}")

    def news(self, path: str = "") -> FakeEndpoint:
        return FakeEndpoint(self.mocker, self.client.news_url(path))

    @property
    def request_count(self) -> int:
        return self.mocker.call_count

    @property
    def last_request(self) -> SentRequest:
        request = self.mocker.last_request
        url = urlparse(request.url)
        return SentRequest(url.path, parse_qs(url.query), request.timeout)
