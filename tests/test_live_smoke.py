"""Bounded smoke tests against the real EDS API; everything else is mocked."""
import allure
import pytest

from tests.support.schema import assert_all_match_schema

TRANSIENT_NETWORK_ERRORS = ["ConnectionError", "Timeout", "RetryError"]


@allure.feature("CO2Emis")
def test_whenGettingConsecutivePages_thenPagesAreDifferent(co2_api):
    # act
    first_page = co2_api.get(limit=5, offset=0).json()
    second_page = co2_api.get(limit=5, offset=5).json()

    # assert
    first_timestamps = [record["Minutes5UTC"] for record in first_page["records"]]
    second_timestamps = [record["Minutes5UTC"] for record in second_page["records"]]
    assert len(first_page["records"]) == 5
    assert len(second_page["records"]) == 5
    # tolerant of a single record drifting in live, continuously updated data
    assert first_timestamps != second_timestamps


@allure.feature("CO2Emis")
def test_givenUnknownDataset_whenGettingIt_thenStatusIsNotOk(eds_client):
    # act
    response = eds_client.get_dataset("NotARealDataset")

    # assert
    assert response.status_code != 200


@allure.feature("Elspotprices")
@pytest.mark.flaky(reruns=2, reruns_delay=5, only_rerun=TRANSIENT_NETWORK_ERRORS)
def test_givenDescendingSort_whenGettingElspotprices_thenPricesAreDescending(elspotprices_api):
    # act
    response = elspotprices_api.get(limit=5, sort="SpotPriceDKK desc")

    # assert
    prices = [record["SpotPriceDKK"] for record in response.json()["records"]]
    assert prices == sorted(prices, reverse=True)


@allure.feature("News")
def test_whenGettingLiveNews_thenEveryItemMatchesSchema(news_api):
    # act
    response = news_api.list()

    # assert
    assert response.status_code == 200
    assert_all_match_schema(response.json(), "news_schema.json")


@allure.feature("News")
def test_whenGettingLiveCalendar_thenEveryEntryMatchesSchemaAndArchiveAgrees(news_api):
    # arrange
    calendar = news_api.calendar().json()
    latest = calendar[0]

    # act
    archived = news_api.archived(date=f"{latest['dateString']}-01-01").json()

    # assert
    assert_all_match_schema(calendar, "news_calendar_schema.json")
    assert len(archived) == latest["numberOfNewsStories"]
    assert all(item["validFrom"].startswith(latest["dateString"]) for item in archived)
