import pytest

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "URL building")

BASE = "http://localhost:9999"


def test_givenBaseUrlWithTrailingSlash_whenBuildingDatasetUrl_thenNoDoubleSlash():
    # arrange
    client = EDSApiClient(base_url=BASE + "/")

    # act
    url = client.dataset_url("CO2Emis")

    # assert
    assert url == f"{BASE}/dataset/CO2Emis"


@pytest.mark.parametrize(
    ("path", "expected_suffix"),
    [
        ("", "/News"),
        ("/actual/", "/News/actual"),
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
    ("path", "encoded"),
    [
        ("../Dataset", "..%2FDataset"),
        ("actual?category=HIGH", "actual%3Fcategory%3DHIGH"),
        ("my path", "my%20path"),
    ],
    ids=["path-traversal", "query", "space"],
)
def test_givenNewsPathWithSpecialCharacters_whenBuildingNewsUrl_thenItStaysOneEncodedPathSegment(
    path, encoded
):
    # arrange
    client = EDSApiClient(base_url=BASE)

    # act
    url = client.news_url(path)

    # assert
    assert url == f"{BASE}/News/{encoded}"


@pytest.mark.parametrize(
    ("dataset", "encoded"),
    [
        ("../News", "..%2FNews"),
        ("my data", "my%20data"),
        ("x?limit=1#top", "x%3Flimit%3D1%23top"),
    ],
    ids=["path-traversal", "space", "query-and-fragment"],
)
def test_givenDatasetNameWithSpecialCharacters_whenBuildingDatasetUrl_thenItStaysOneEncodedSegment(
    dataset, encoded
):
    # arrange
    client = EDSApiClient(base_url=BASE)

    # act
    url = client.dataset_url(dataset)

    # assert
    assert url == f"{BASE}/dataset/{encoded}"


def test_givenDatasetNameWithSlash_whenGettingDataset_thenRequestPathKeepsTheEncodedSlash(
    eds, eds_client
):
    # arrange
    api = DatasetApi(eds_client, "../News")
    eds.dataset("../News").answers()

    # act
    api.get()

    # assert
    assert eds.last_request.path == "/dataset/..%2FNews"
