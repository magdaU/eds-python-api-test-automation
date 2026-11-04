import pytest

from tests.support.allure_labels import labels

pytestmark = labels("Dataset API", "Boundary values")


@pytest.mark.parametrize("limit", [0, 1])
def test_givenLimitAtBoundary_whenGettingDataset_thenLimitIsSentUnchanged(
    eds, dataset, dataset_api, limit
):
    # arrange
    eds.dataset(dataset.name).answers()

    # act
    dataset_api.get(limit=limit)

    # assert
    assert eds.last_request.query["limit"] == [str(limit)]


def test_givenZeroOffset_whenGettingDataset_thenOffsetIsSentUnchanged(eds, dataset, dataset_api):
    # arrange
    eds.dataset(dataset.name).answers()

    # act
    dataset_api.get(offset=0)

    # assert
    assert eds.last_request.query["offset"] == ["0"]


def test_givenNoParameters_whenGettingDataset_thenNoQueryStringIsSent(eds, dataset, dataset_api):
    # arrange
    eds.dataset(dataset.name).answers()

    # act
    dataset_api.get()

    # assert
    assert eds.last_request.query == {}


def test_givenNegativeOffset_whenGettingDataset_thenValueIsSentAndServerRejectionIsReturned(
    eds, dataset, dataset_api
):
    # arrange
    eds.dataset(dataset.name).answers(status=400, json={"error": "invalid offset"})

    # act
    response = dataset_api.get(offset=-1)

    # assert
    assert eds.last_request.query["offset"] == ["-1"]
    assert response.status_code == 400
