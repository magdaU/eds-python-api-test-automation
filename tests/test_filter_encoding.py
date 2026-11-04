import json

from tests.support.allure_labels import labels

pytestmark = labels("Dataset API", "Filtering")


def test_givenNonAsciiFilter_whenGettingDataset_thenFilterRoundTripsThroughJson(
    eds, dataset, dataset_api
):
    # arrange
    eds.dataset(dataset.name).answers()
    filters = {"PriceArea": "Ærø Ø å"}

    # act
    dataset_api.get(filters=filters)

    # assert
    assert json.loads(eds.last_request.query["filter"][0]) == filters


def test_givenEmptyFilters_whenGettingDataset_thenEmptyJsonObjectIsSent(eds, dataset, dataset_api):
    # arrange
    eds.dataset(dataset.name).answers()

    # act
    dataset_api.get(filters={})

    # assert
    assert eds.last_request.query["filter"] == ["{}"]


def test_givenNumericFilterValue_whenGettingDataset_thenItIsSentAsJsonNumber(
    eds, dataset, dataset_api
):
    # arrange
    eds.dataset(dataset.name).answers()
    filters = {dataset.value_field: 12}

    # act
    dataset_api.get(filters=filters)

    # assert
    assert json.loads(eds.last_request.query["filter"][0]) == filters
