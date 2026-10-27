import pytest

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
