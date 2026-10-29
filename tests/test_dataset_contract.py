from urllib.parse import urlparse

import allure
from tests.support.allure_labels import labels
from tests.support.mocks import load_mock, records_response, sent_query
from tests.support.schema import assert_matches_schema
from tests.support.scripted_server import api_for

pytestmark = labels("Dataset API", "Response contract")


def test_givenSampleResponse_whenValidatingAgainstSchema_thenSchemaIsSatisfied(dataset):
    # arrange
    allure.dynamic.feature(dataset.name)
    sample = load_mock(dataset.sample_response_file)

    # act / assert
    assert_matches_schema(sample, dataset.schema_file)


def test_givenLimitAndFilter_whenGettingDataset_thenRequestTargetsTheDatasetWithThoseParameters(
    dataset, dataset_api, requests_mock
):
    # arrange
    allure.dynamic.feature(dataset.name)
    requests_mock.get(dataset_api.url, json=records_response([]))

    # act
    dataset_api.get(limit=3, filters={"PriceArea": "DK2"})

    # assert
    assert urlparse(requests_mock.last_request.url).path == f"/dataset/{dataset.name}"
    assert sent_query(requests_mock) == {"limit": ["3"], "filter": ['{"PriceArea":"DK2"}']}


def test_givenDataset_whenGettingMetadata_thenRequestGoesToItsMetaPathWithoutParameters(dataset, dataset_api, requests_mock):
    # arrange
    allure.dynamic.feature(dataset.name)
    requests_mock.get(f"{dataset_api.client.base_url}/meta/dataset/{dataset.name}", json={})

    # act
    dataset_api.metadata()

    # assert
    assert urlparse(requests_mock.last_request.url).path == f"/meta/dataset/{dataset.name}"
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
