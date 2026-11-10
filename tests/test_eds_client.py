import pytest
import requests

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient, RetryConfig
from tests.support.allure_labels import labels

pytestmark = labels("Dataset API", "Request methods", "critical")


def test_givenDataset_whenGettingIt_thenRequestIsHttpGet(requests_mock, eds, dataset, dataset_api):
    # arrange
    eds.dataset(dataset.name).answers()

    # act
    dataset_api.get()

    # assert
    # the guide: "The restful API is a synchronous interface with Http Get."
    assert requests_mock.last_request.method == "GET"


def test_givenLimitOffsetAndSort_whenGettingDataset_thenParametersAreJoinedByAmpersand(
    requests_mock, eds, dataset, dataset_api
):
    # arrange
    eds.dataset(dataset.name).answers()

    # act
    dataset_api.get(limit=3, offset=6, sort=dataset.required_field)

    # assert
    # the guide: "Parameter Name = Parameter Value, where each pair of parameter name and value
    # are separated by &."
    query = requests_mock.last_request.url.split("?", 1)[1]
    assert query == f"limit=3&offset=6&sort={dataset.required_field}"


def test_givenDataset_whenGettingMetadata_thenRequestIsHttpGetOnTheMetaPath(
    requests_mock, eds, dataset, dataset_api
):
    # arrange
    eds.metadata(dataset.name).answers(json={})

    # act
    dataset_api.metadata()

    # assert
    # the guide: "or to get metadata: .../meta/dataset/{dataset | group | organization}"
    assert requests_mock.last_request.method == "GET"
    # requests_mock compares the path in lower case
    assert requests_mock.last_request.path == f"/meta/dataset/{dataset.name.lower()}"


def test_givenServerSlowerThanTheTimeout_whenGettingDataset_thenConnectionErrorNamesTheReadTimeout(
    scripted_server,
):
    # arrange
    server = scripted_server(200, delay=0.5)
    client = EDSApiClient(
        base_url=server.url, timeout=0.1, retry=RetryConfig(max_retries=0, backoff_factor=0)
    )

    # act / assert
    # not in the guide: a client setting, kept because a request that never ends is a client defect
    with pytest.raises(requests.exceptions.ConnectionError, match="Read timed out"):
        DatasetApi(client, "CO2Emis").get()
