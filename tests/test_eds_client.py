import pytest
import requests

from client.dataset_api import DatasetApi
from client.eds_client import DEFAULT_TIMEOUT, EDSApiClient, RetryConfig
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "Client configuration")


def test_whenCreatingClientWithDefaults_thenDefaultTimeoutIsUsedPerRequest(eds):
    # arrange
    client = EDSApiClient()
    eds.dataset("CO2Emis").answers()

    # act
    client.get_dataset("CO2Emis")

    # assert
    assert eds.last_request.timeout == DEFAULT_TIMEOUT


def test_givenCustomTimeout_whenGettingDataset_thenItIsPassedToTheRequest(eds):
    # arrange
    client = EDSApiClient(timeout=3)
    eds.dataset("CO2Emis").answers()

    # act
    client.get_dataset("CO2Emis")

    # assert
    assert eds.last_request.timeout == 3


def test_givenServerSlowerThanTheTimeout_whenGettingDataset_thenConnectionErrorNamesTheReadTimeout(
    scripted_server,
):
    # arrange
    server = scripted_server(200, delay=0.5)
    client = EDSApiClient(
        base_url=server.url, timeout=0.1, retry=RetryConfig(max_retries=0, backoff_factor=0)
    )

    # act / assert
    with pytest.raises(requests.exceptions.ConnectionError, match="Read timed out"):
        DatasetApi(client, "CO2Emis").get()


def test_whenUsingClientAsContextManager_thenSessionIsClosedOnExit(monkeypatch):
    # arrange
    client = EDSApiClient()
    closed = []
    monkeypatch.setattr(client.session, "close", lambda: closed.append(True))

    # act
    with client:
        pass

    # assert
    assert closed == [True]


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.client.get_dataset("CO2Emis", 5),
        lambda api: api.get(5),
        lambda api: api.records(5),
    ],
    ids=["client-get-dataset", "api-get", "api-records"],
)
def test_givenPositionalQueryArgument_whenGettingDataset_thenTypeErrorIsRaised(co2_api, call):
    # act / assert
    with pytest.raises(TypeError, match="positional"):
        call(co2_api)
