import allure
from tests.support.allure_labels import labels
from tests.support.datasets import CO2EMIS_DATASET
from tests.support.mocks import load_mock, sent_path, sent_query
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
    co2_api_answering_empty, requests_mock
):
    # act
    co2_api_answering_empty.get(limit=3, filters={"PriceArea": "DK2"})

    # assert
    assert sent_path(requests_mock) == f"/dataset/{CO2EMIS_DATASET.name}"
    assert sent_query(requests_mock) == {"limit": ["3"], "filter": ['{"PriceArea":"DK2"}']}


def test_givenDataset_whenGettingMetadata_thenRequestGoesToItsMetaPathWithoutParameters(co2_api, requests_mock):
    # arrange
    requests_mock.get(f"{co2_api.client.base_url}/meta/dataset/{CO2EMIS_DATASET.name}", json={})

    # act
    co2_api.metadata()

    # assert
    assert sent_path(requests_mock) == f"/meta/dataset/{CO2EMIS_DATASET.name}"
    assert sent_query(requests_mock) == {}


def test_givenSuccessfulResponse_whenGettingDataset_thenStatusJsonContentTypeAndBodyArriveUnchanged(scripted_server):
    # arrange
    server = scripted_server(200)

    # act
    response = api_for(server).get()

    # assert
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.json() == {"records": [], "total": 0}
