from tests.support.allure_labels import labels

pytestmark = labels("Dataset API", "Response contract", "critical")


def test_givenLimitAndFilter_whenGettingDataset_thenRequestTargetsTheDatasetWithThoseParameters(
    eds, dataset, dataset_api
):
    # arrange
    eds.dataset(dataset.name).answers()

    # act
    dataset_api.get(limit=3, filters={"PriceArea": ["DK2"]})

    # assert
    assert eds.last_request.path == f"/dataset/{dataset.name}"
    assert eds.last_request.query == {"limit": ["3"], "filter": ['{"PriceArea":["DK2"]}']}


def test_givenDataset_whenGettingMetadata_thenRequestGoesToItsMetaPathWithoutParameters(
    eds, dataset, dataset_api
):
    # arrange
    eds.metadata(dataset.name).answers(json={})

    # act
    dataset_api.metadata()

    # assert
    assert eds.last_request.path == f"/meta/dataset/{dataset.name}"
    assert eds.last_request.query == {}
