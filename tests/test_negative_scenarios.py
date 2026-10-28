import socket

import pytest
import requests

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "Negative scenarios")

# requests_mock replaces how the session dispatches requests entirely, so the
# custom HTTPAdapter/Retry mounted on EDSApiClient's session never runs against
# a mocked response (verified: any mocked status code yields call_count == 1,
# retryable or not). Only exceptions are mocked here; statuses, including 4xx that
# must not be retried, run against a real local server in test_retry_behavior.py.


def test_givenConnectionTimeout_whenGettingDataset_thenTimeoutIsRaised(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, exc=requests.exceptions.ConnectTimeout)

    # act / assert
    with pytest.raises(requests.exceptions.ConnectTimeout):
        co2_api.get()


def test_givenNothingListening_whenGettingDataset_thenConnectionErrorIsRaised():
    # arrange
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]
    api = DatasetApi(EDSApiClient(base_url=f"http://127.0.0.1:{free_port}", max_retries=1, backoff_factor=0), "CO2Emis")

    # act / assert
    with pytest.raises(requests.exceptions.ConnectionError):
        api.get()
