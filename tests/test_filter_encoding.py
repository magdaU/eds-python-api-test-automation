import json

import pytest

from tests.support.allure_labels import labels
from tests.support.mocks import records_response, sent_query

pytestmark = labels("Dataset API", "Filtering")


def sent_filter(requests_mock):
    return json.loads(sent_query(requests_mock)["filter"][0])


@pytest.mark.parametrize(
    "filters",
    [
        {"PriceArea": "DK1", "SpotPriceDKK": "12.5"},
        {"PriceArea": "Ærø Ø å"},
        {"PriceArea": "DK1,DK2"},
        {"PriceArea": ["DK1", "DK2"]},
        {"PriceArea": 'DK"1\\x'},
    ],
    ids=["two-keys", "non-ascii", "comma-in-value", "list-of-values", "quote-and-backslash"],
)
def test_givenFilters_whenGettingDataset_thenFilterRoundTripsThroughJson(elspotprices_api, requests_mock, filters):
    # arrange
    requests_mock.get(elspotprices_api.url, json=records_response([]))

    # act
    elspotprices_api.get(filters=filters)

    # assert
    assert sent_filter(requests_mock) == filters


def test_givenEmptyFilters_whenGettingDataset_thenEmptyJsonObjectIsSent(elspotprices_api, requests_mock):
    # arrange
    requests_mock.get(elspotprices_api.url, json=records_response([]))

    # act
    elspotprices_api.get(filters={})

    # assert
    assert sent_query(requests_mock)["filter"] == ["{}"]


def test_givenNumericFilterValue_whenGettingDataset_thenItIsSentAsJsonNumber(elspotprices_api, requests_mock):
    # arrange
    requests_mock.get(elspotprices_api.url, json=records_response([]))

    # act
    elspotprices_api.get(filters={"SpotPriceDKK": 12})

    # assert
    assert sent_filter(requests_mock) == {"SpotPriceDKK": 12}
