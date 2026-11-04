import pytest

from tests.support.allure_labels import labels

pytestmark = labels("Dataset API", "Parameter combinations")

# Decision table over the four optional parameters: each row is one rule,
# the expected value says which query parameters must reach the API.
# PriceArea is a column of every dataset under test, so the rows hold for each of them.
COMBINATIONS = [
    (
        {"offset": 10, "filters": {"PriceArea": "DK1"}},
        {"offset": ["10"], "filter": ['{"PriceArea":"DK1"}']},
    ),
    (
        {"limit": 7, "offset": 3, "sort": "PriceArea", "filters": {"PriceArea": "DK2"}},
        {
            "limit": ["7"],
            "offset": ["3"],
            "sort": ["PriceArea"],
            "filter": ['{"PriceArea":"DK2"}'],
        },
    ),
]


@pytest.mark.parametrize(("arguments", "expected_query"), COMBINATIONS)
def test_givenParameterCombination_whenGettingDataset_thenExactlyThoseParametersAreSent(
    eds, dataset, dataset_api, arguments, expected_query
):
    # arrange
    eds.dataset(dataset.name).answers()

    # act
    dataset_api.get(**arguments)

    # assert
    assert eds.last_request.query == expected_query
