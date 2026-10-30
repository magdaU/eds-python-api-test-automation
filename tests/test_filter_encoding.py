import json

from tests.support.allure_labels import labels
from tests.support.mocks import sent_query

pytestmark = labels("Dataset API", "Filtering")


def sent_filter(requests_mock):
    return json.loads(sent_query(requests_mock)["filter"][0])


def test_givenNonAsciiFilter_whenGettingDataset_thenFilterRoundTripsThroughJson(
    dayaheadprices_api_answering_empty, requests_mock
):
    # arrange
    filters = {"PriceArea": "Ærø Ø å"}
    # act
    dayaheadprices_api_answering_empty.get(filters=filters)

    # assert
    assert sent_filter(requests_mock) == filters


def test_givenEmptyFilters_whenGettingDataset_thenEmptyJsonObjectIsSent(dayaheadprices_api_answering_empty, requests_mock):
    # act
    dayaheadprices_api_answering_empty.get(filters={})

    # assert
    assert sent_query(requests_mock)["filter"] == ["{}"]


def test_givenNumericFilterValue_whenGettingDataset_thenItIsSentAsJsonNumber(dayaheadprices_api_answering_empty, requests_mock):
    # act
    dayaheadprices_api_answering_empty.get(filters={"DayAheadPriceDKK": 12})

    # assert
    assert sent_filter(requests_mock) == {"DayAheadPriceDKK": 12}
