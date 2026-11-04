"""Low-load live checks of how the real EDS API treats edge and invalid input.

One request per test, `limit=1`, and a pause before each. Note: `limit=-1` is
deliberately NOT tested live -- the API treats it as "no limit" and returns the
whole dataset (millions of records).
"""

import time

import pytest

import allure
from tests.support.assertions import (
    assert_bad_request_mentioning,
    assert_bad_request_naming_parameter,
    assert_no_records,
    describe_response,
)
from tests.support.live import (
    TRANSIENT_NETWORK_ERRORS,
    live_eds_client,  # noqa: F401
)

pytestmark = [
    pytest.mark.live,
    allure.epic("Live API"),
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
    assert_bad_request_mentioning(response, "offset")


@allure.feature("CO2Emis")
def test_givenUnknownSortColumn_whenGettingDataset_thenBadRequestMentionsSort(co2_api):
    # act
    response = co2_api.get(limit=1, sort="NoSuchColumn")

    # assert
    assert_bad_request_mentioning(response, "sort")


@allure.feature("CO2Emis")
def test_givenUnknownFilterColumn_whenGettingDataset_thenBadRequestMentionsColumn(co2_api):
    # act
    response = co2_api.get(limit=1, filters={"NoSuchColumn": "x"})

    # assert
    assert_bad_request_mentioning(response, "column")


@allure.feature("CO2Emis")
def test_givenFilterMatchingNothing_whenGettingDataset_thenResultIsEmptyAndFilterIsEchoed(co2_api):
    # act
    response = co2_api.get(limit=1, filters={"PriceArea": "ZZ9"})

    # assert
    assert_no_records(response)
    body = response.json()
    assert body["total"] == 0, describe_response(response)
    assert body["filters"] == '{"PriceArea":"ZZ9"}', describe_response(response)


@allure.feature("CO2Emis")
def test_givenOffsetFarBeyondData_whenGettingDataset_thenResultIsEmpty(co2_api):
    # act
    response = co2_api.get(limit=1, offset=100_000_000)

    # assert
    assert_no_records(response)


@allure.feature("News")
def test_givenUnknownCategory_whenGettingActualNews_thenNoContentIsReturned(news_api):
    # act
    response = news_api.actual(category="NOT_A_CATEGORY")

    # assert
    assert response.status_code == 204, describe_response(response)
    assert response.text == "", describe_response(response)


@allure.feature("News")
def test_givenNoCategory_whenGettingActualNews_thenBadRequestNamesCategory(news_api):
    # act
    response = news_api.actual()

    # assert
    assert_bad_request_naming_parameter(response, "category")


@allure.feature("News")
def test_givenInvalidDate_whenGettingArchivedNews_thenBadRequestNamesDate(news_api):
    # act
    response = news_api.archived(date="bogus")

    # assert
    assert_bad_request_naming_parameter(response, "date")


@allure.feature("News")
def test_givenUnknownNewsPath_whenGettingNews_thenNotFoundIsReturned(news_api):
    # act
    response = news_api.get("nosuchpath")

    # assert
    assert response.status_code == 404, describe_response(response)


@allure.feature("News")
def test_givenSubPathBelowCalendar_whenGettingNews_thenNotFoundIsReturned(news_api):
    # act
    response = news_api.get("calendar/extra")

    # assert
    assert response.status_code == 404, describe_response(response)


@allure.feature("News")
def test_givenUnknownParameter_whenGettingCalendar_thenItIsIgnored(news_api):
    # act
    response = news_api.get("calendar", {"bogus": "1"})

    # assert
    assert response.status_code == 200, describe_response(response)
    body = response.json()
    assert body, describe_response(response)
    assert set(body[0]) == {"dateString", "numberOfNewsStories"}, describe_response(response)


@allure.feature("News")
def test_givenUnknownParameter_whenGettingNewsList_thenItIsIgnored(news_api):
    # act
    response = news_api.get(params={"bogus": "1"})

    # assert
    assert response.status_code == 200, describe_response(response)
    assert isinstance(response.json(), list), describe_response(response)


@allure.feature("News")
def test_givenDifferentCase_whenGettingCalendar_thenPathIsStillResolved(news_api):
    # act
    response = news_api.get("Calendar")

    # assert
    assert response.status_code == 200, describe_response(response)
    assert response.json()[0]["dateString"], describe_response(response)
