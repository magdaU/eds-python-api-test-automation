from client.eds_client import DEFAULT_TIMEOUT, RETRYABLE_STATUS_CODES, EDSApiClient, RetryConfig
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "Client configuration")


def test_whenCreatingClientWithDefaults_thenDefaultRetryConfigurationIsApplied():
    # arrange
    client = EDSApiClient()

    # act
    adapter = client.session.get_adapter(client.base_url)

    # assert
    assert adapter.max_retries.total == 3
    assert adapter.max_retries.backoff_factor == 1.0
    assert set(adapter.max_retries.status_forcelist) == set(RETRYABLE_STATUS_CODES)


def test_givenCustomRetrySettings_whenCreatingClient_thenTheyAreApplied():
    # arrange
    client = EDSApiClient(retry=RetryConfig(max_retries=5, backoff_factor=2.0))

    # act
    adapter = client.session.get_adapter(client.base_url)

    # assert
    assert adapter.max_retries.total == 5
    assert adapter.max_retries.backoff_factor == 2.0


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
