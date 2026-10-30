import pytest

from tests.support.allure_labels import labels
from tests.support.mocks import records_response, sent_query

pytestmark = labels("Dataset API", "Parameter combinations")

# Decision table over the four optional parameters: each row is one rule,
# the expected value says which query parameters must reach the API.
COMBINATIONS = [
    ({"offset": 10, "filters": {"PriceArea": "DK1"}}, {"offset": ["10"], "filter": ['{"PriceArea":"DK1"}']}),
    (
        {"limit": 7, "offset": 3, "sort": "Minutes5UTC", "filters": {"PriceArea": "DK2"}},
        {"limit": ["7"], "offset": ["3"], "sort": ["Minutes5UTC"], "filter": ['{"PriceArea":"DK2"}']},
    ),
]


@pytest.mark.parametrize(("arguments", "expected_query"), COMBINATIONS)
def test_givenParameterCombination_whenGettingDataset_thenExactlyThoseParametersAreSent(
    co2_api, requests_mock, arguments, expected_query
):
    # arrange
    requests_mock.get(co2_api.url, json=records_response([]))

    # act
    co2_api.get(**arguments)

    # assert
    assert sent_query(requests_mock) == expected_query
