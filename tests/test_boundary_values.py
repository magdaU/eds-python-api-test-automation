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
