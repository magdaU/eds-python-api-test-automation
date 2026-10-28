"""Bounded smoke tests against the real EDS API; everything else is mocked."""

import pytest

import allure
from tests.support.schema import assert_all_match_schema, assert_matches_schema

pytestmark = [pytest.mark.live, allure.epic("Live API")]


@allure.feature("CO2Emis")
def test_whenGettingConsecutivePages_thenPagesAreDifferent(co2_api):
    # act
    first_page = co2_api.get(limit=5, offset=0).json()
    second_page = co2_api.get(limit=5, offset=5).json()

    # assert
    # a record is one timestamp per price area, so the timestamp alone is not unique
    first_records = {(record["Minutes5UTC"], record["PriceArea"]) for record in first_page["records"]}
    second_records = {(record["Minutes5UTC"], record["PriceArea"]) for record in second_page["records"]}
    assert len(first_page["records"]) == 5
    assert len(second_page["records"]) == 5
    # live data keeps arriving, so a few records may shift between the two calls; identical pages mean offset was ignored
    assert len(first_records | second_records) > 5


@allure.feature("CO2Emis")
def test_givenUnknownDataset_whenGettingIt_thenNotFoundNamesTheDataset(eds_client):
    # act
    response = eds_client.get_dataset("NotARealDataset")

    # assert
    assert response.status_code == 404
    assert "NotARealDataset" in response.text


@allure.feature("Elspotprices")
def test_givenDescendingSort_whenGettingElspotprices_thenPricesAreDescending(elspotprices_latest):
    # act
    response = elspotprices_latest

    # assert
    prices = [record["SpotPriceDKK"] for record in response.json()["records"]]
    assert response.status_code == 200
    assert len(prices) == 5
    assert prices == sorted(prices, reverse=True)


@allure.feature("News")
def test_whenGettingLiveNews_thenEveryItemMatchesSchema(news_api):
    # act
    response = news_api.list()

    # assert
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # /News lists only current news and may legitimately be empty, so it can't use the helper that rejects an empty list;
    # the archive test below validates the same schema against real items
    for item in response.json():
        assert_matches_schema(item, "news_schema.json")


@allure.feature("News")
def test_whenGettingLiveCalendar_thenEveryEntryMatchesSchemaAndArchiveAgrees(news_api):
    # arrange
    calendar_response = news_api.calendar()
    calendar = calendar_response.json()
    years_with_news = [entry for entry in calendar if entry["numberOfNewsStories"] > 0]
    assert calendar_response.status_code == 200 and years_with_news, "the calendar must list a year with news to compare"
    latest = max(years_with_news, key=lambda entry: entry["dateString"])

    # act
    archived_response = news_api.archived(date=f"{latest['dateString']}-01-01")
    archived = archived_response.json()

    # assert
    assert archived_response.status_code == 200
    assert_all_match_schema(calendar, "news_calendar_schema.json")
    assert_all_match_schema(archived, "news_schema.json")
    assert len(archived) == latest["numberOfNewsStories"]
    assert all(item["validFrom"].startswith(latest["dateString"]) for item in archived)
