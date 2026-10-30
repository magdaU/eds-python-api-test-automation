"""Bounded smoke tests against the real EDS API; everything else is mocked."""

import re

import pytest

import allure
from models.co2emis import CO2EmisRecord
from tests.support.live import TRANSIENT_NETWORK_ERRORS
from tests.support.schema import assert_all_match_schema, assert_matches_schema

pytestmark = [
    pytest.mark.live,
    allure.epic("Live API"),
    pytest.mark.flaky(reruns=1, reruns_delay=5, only_rerun=TRANSIENT_NETWORK_ERRORS),
]


# ISO 8601 duration such as PT5M or P1D; EDS writes "N/A" for a dataset that is no longer updated (as for Elspotprices)
UPDATE_INTERVAL = re.compile(r"P(?=\d|T\d)(\d+[YMWD])*(T(\d+[HMS])+)?")


def test_whenGettingDatasetMetadata_thenTheDatasetIsStillPublishedAndUpdated(dataset, dataset_api):
    # arrange
    allure.dynamic.feature(dataset.name)

    # act
    response = dataset_api.metadata()

    # assert
    metadata = response.json()
    assert response.status_code == 200
    assert metadata["datasetName"] == dataset.name
    assert metadata["active"] is True
    assert "discontinued" not in metadata["title"].lower(), metadata["title"]
    assert UPDATE_INTERVAL.fullmatch(metadata["updateFrequency"]), f"update frequency is {metadata['updateFrequency']!r}"


@allure.feature("CO2Emis")
def test_whenGettingRecords_thenTheyAreTypedModelObjects(co2_api):
    # act
    records = co2_api.records(limit=3)

    # assert
    assert len(records) == 3
    assert all(isinstance(record, CO2EmisRecord) for record in records)


@allure.feature("CO2Emis")
def test_givenOldestFirstSort_whenGettingConsecutivePages_thenTogetherTheyEqualOneLargerPage(co2_api):
    # arrange
    # the oldest records never change, so unlike the newest ones the pages cannot shift between the calls
    oldest_first = {"sort": "Minutes5UTC asc, PriceArea asc"}

    # act
    first_page = co2_api.get(limit=5, offset=0, **oldest_first).json()["records"]
    second_page = co2_api.get(limit=5, offset=5, **oldest_first).json()["records"]
    one_page = co2_api.get(limit=10, offset=0, **oldest_first).json()["records"]

    # assert
    assert len(one_page) == 10
    assert first_page + second_page == one_page


@allure.feature("CO2Emis")
def test_givenUnknownDataset_whenGettingIt_thenNotFoundNamesTheDataset(eds_client):
    # act
    response = eds_client.get_dataset("NotARealDataset")

    # assert
    assert response.status_code == 404
    assert "NotARealDataset" in response.text


@allure.feature("CO2Emis")
@pytest.mark.parametrize(
    ("filters", "expected_areas"),
    [
        ({"PriceArea": "DK1"}, {"DK1"}),
        ({"PriceArea": ["DK1", "DK2"]}, {"DK1", "DK2"}),
    ],
    ids=["one-value", "two-values-are-or"],
)
def test_givenPriceAreaFilter_whenGettingCo2Emis_thenOnlyTheRequestedAreasAreReturned(co2_api, filters, expected_areas):
    # act
    response = co2_api.get(limit=50, filters=filters)

    # assert
    areas = {record["PriceArea"] for record in response.json()["records"]}
    assert response.status_code == 200
    # 50 records span many timestamps, so a late-publishing area still appears; a filter on two areas must return both
    assert areas == expected_areas


@allure.feature("DayAheadPrices")
def test_givenDescendingSort_whenGettingDayAheadPrices_thenPricesAreDescending(dayaheadprices_latest):
    # act
    response = dayaheadprices_latest

    # assert
    prices = [record["DayAheadPriceDKK"] for record in response.json()["records"]]
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
    assert calendar_response.status_code == 200
    assert years_with_news, "the calendar must list a year with news to compare"
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
