import allure
from tests.support.allure_labels import labels
from tests.support.mocks import load_mock
from tests.support.schema import assert_matches_schema
from tests.support.scripted_server import api_for

pytestmark = labels("Dataset API", "Response contract", "critical")


def test_givenSampleResponse_whenValidatingAgainstSchema_thenSchemaIsSatisfied(dataset):
    # arrange
    allure.dynamic.feature(dataset.name)
    sample = load_mock(dataset.sample_response_file)

    # act / assert
    assert_matches_schema(sample, dataset.schema_file)


def test_givenLimitAndFilter_whenGettingDataset_thenRequestTargetsTheDatasetWithThoseParameters(
    eds, dataset, dataset_api
):
    # arrange
    eds.dataset(dataset.name).answers()

    # act
    dataset_api.get(limit=3, filters={"PriceArea": "DK2"})

    # assert
    assert eds.last_request.path == f"/dataset/{dataset.name}"
    assert eds.last_request.query == {"limit": ["3"], "filter": ['{"PriceArea":"DK2"}']}


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


def test_givenSuccessfulResponse_whenGettingDataset_thenStatusJsonContentTypeAndBodyArriveUnchanged(
    scripted_server,
):
    # arrange
    server = scripted_server(200)

    # act
    response = api_for(server).get()

    # assert
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.json() == {"records": [], "total": 0}
