import json

from tests.support.allure_labels import labels

pytestmark = labels("Dataset API", "Filtering")


def test_givenNonAsciiFilter_whenGettingDataset_thenFilterRoundTripsThroughJson(
    eds, dataset, dataset_api
):
    # arrange
    eds.dataset(dataset.name).answers()
    filters = {"PriceArea": ["Ærø Ø å"]}

    # act
    dataset_api.get(filters=filters)

    # assert
    assert json.loads(eds.last_request.query["filter"][0]) == filters
