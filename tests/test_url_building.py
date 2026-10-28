from urllib.parse import urlparse

import pytest

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "URL building")

BASE = "http://localhost:9999"


@pytest.mark.parametrize("base_url", [BASE, BASE + "/"])
def test_givenBaseUrlWithOrWithoutTrailingSlash_whenBuildingDatasetUrl_thenNoDoubleSlash(base_url):
    # arrange
    client = EDSApiClient(base_url=base_url)

    # act
    url = client.dataset_url("CO2Emis")

    # assert
    assert url == f"{BASE}/dataset/CO2Emis"


@pytest.mark.parametrize(
    "path, expected_suffix",
    [
        ("", "/News"),
        ("actual", "/News/actual"),
        ("/actual", "/News/actual"),
        ("calendar/", "/News/calendar"),
    ],
)
def test_givenNewsPath_whenBuildingNewsUrl_thenSlashesAreNormalized(path, expected_suffix):
    # arrange
    client = EDSApiClient(base_url=BASE)

    # act
    url = client.news_url(path)

    # assert
    assert url == BASE + expected_suffix


@pytest.mark.parametrize(
    "dataset, encoded",
    [
        ("../News", "..%2FNews"),
        ("my data", "my%20data"),
        ("x?limit=1#top", "x%3Flimit%3D1%23top"),
    ],
    ids=["path-traversal", "space", "query-and-fragment"],
)
def test_givenDatasetNameWithSpecialCharacters_whenBuildingDatasetUrl_thenItStaysOneEncodedPathSegment(dataset, encoded):
    # arrange
    client = EDSApiClient(base_url=BASE)

    # act
    url = client.dataset_url(dataset)

    # assert
    assert url == f"{BASE}/dataset/{encoded}"


def test_givenDatasetNameWithSlash_whenGettingDataset_thenRequestPathKeepsTheEncodedSlash(requests_mock):
    # arrange
    api = DatasetApi(EDSApiClient(base_url=BASE), "../News")
    requests_mock.get(api.url, json={"records": [], "total": 0})

    # act
    api.get()

    # assert
    assert urlparse(requests_mock.last_request.url).path == "/dataset/..%2FNews"
