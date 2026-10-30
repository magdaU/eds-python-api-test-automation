import pytest
import requests

from client.dataset_api import DatasetApi
from client.eds_client import DEFAULT_TIMEOUT, EDSApiClient, RetryConfig
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "Client configuration")


def test_whenCreatingClientWithDefaults_thenDefaultTimeoutIsUsedPerRequest(requests_mock):
    # arrange
    client = EDSApiClient()
    requests_mock.get(client.dataset_url("CO2Emis"), json={"records": []})

    # act
    client.get_dataset("CO2Emis")

    # assert
    assert requests_mock.last_request.timeout == DEFAULT_TIMEOUT


def test_givenCustomTimeout_whenGettingDataset_thenItIsPassedToTheRequest(requests_mock):
    # arrange
    client = EDSApiClient(timeout=3)
    requests_mock.get(client.dataset_url("CO2Emis"), json={"records": []})

    # act
    client.get_dataset("CO2Emis")

    # assert
    assert requests_mock.last_request.timeout == 3


def test_givenServerSlowerThanTheTimeout_whenGettingDataset_thenConnectionErrorNamesTheReadTimeout(scripted_server):
    # arrange
    server = scripted_server(200, delay=0.5)
    client = EDSApiClient(base_url=server.url, timeout=0.1, retry=RetryConfig(max_retries=0, backoff_factor=0))

    # act / assert
    with pytest.raises(requests.exceptions.ConnectionError, match="Read timed out"):
        DatasetApi(client, "CO2Emis").get()
