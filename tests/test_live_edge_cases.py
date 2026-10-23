"""Low-load live checks of how the real EDS API treats edge and invalid input.

One request per test, `limit=1`, and a pause before each. Note: `limit=-1` is
deliberately NOT tested live -- the API treats it as "no limit" and returns the
whole dataset (millions of records).
"""
import time

import allure
import pytest

from tests.support.live import TRANSIENT_NETWORK_ERRORS

pytestmark = [
    pytest.mark.live,
    pytest.mark.flaky(reruns=1, reruns_delay=5, only_rerun=TRANSIENT_NETWORK_ERRORS),
]


@pytest.fixture(autouse=True)
def pause_between_live_requests():
    time.sleep(1)


@allure.feature("CO2Emis")
def test_givenNegativeOffset_whenGettingDataset_thenBadRequestMentionsOffset(co2_api):
    # act
    response = co2_api.get(limit=1, offset=-1)

    # assert
    assert response.status_code == 400
    assert "offset" in response.text.lower()


@allure.feature("CO2Emis")
def test_givenUnknownSortColumn_whenGettingDataset_thenBadRequestMentionsSort(co2_api):
    # act
    response = co2_api.get(limit=1, sort="NoSuchColumn")

    # assert
    assert response.status_code == 400
    assert "sort" in response.text.lower()


@allure.feature("CO2Emis")
def test_givenUnknownFilterColumn_whenGettingDataset_thenBadRequestMentionsColumn(co2_api):
    # act
    response = co2_api.get(limit=1, filters={"NoSuchColumn": "x"})

    # assert
    assert response.status_code == 400
    assert "column" in response.text.lower()


@allure.feature("CO2Emis")
def test_givenFilterMatchingNothing_whenGettingDataset_thenResultIsEmptyAndFilterIsEchoed(co2_api):
    # act
    response = co2_api.get(limit=1, filters={"PriceArea": "ZZ9"})

    # assert
    body = response.json()
    assert response.status_code == 200
    assert body["records"] == []
    assert body["total"] == 0
    assert body["filters"] == '{"PriceArea":"ZZ9"}'


@allure.feature("CO2Emis")
def test_givenOffsetFarBeyondData_whenGettingDataset_thenResultIsEmpty(co2_api):
    # act
    response = co2_api.get(limit=1, offset=100_000_000)

    # assert
    assert response.status_code == 200
    assert response.json()["records"] == []


@allure.feature("News")
def test_givenUnknownCategory_whenGettingActualNews_thenNoContentIsReturned(news_api):
    # act
    response = news_api.actual(category="NOT_A_CATEGORY")

    # assert
    assert response.status_code == 204
    assert response.text == ""


@allure.feature("News")
def test_givenUnknownNewsPath_whenGettingNews_thenNotFoundIsReturned(news_api):
    # act
    response = news_api.get("nosuchpath")

    # assert
    assert response.status_code == 404
