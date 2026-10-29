import socket

import pytest
import requests

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient, RetryConfig
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "Negative scenarios")

# requests_mock replaces how the session dispatches requests entirely, so the
# custom HTTPAdapter/Retry mounted on EDSApiClient's session never runs against
# a mocked response. Statuses, including 4xx that must not be retried, run against
# a real local server in test_retry_behavior.py; the request timeout is checked in test_eds_client.py.


def test_givenNothingListening_whenGettingDataset_thenConnectionErrorIsRaised():
    # arrange
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]
    client = EDSApiClient(base_url=f"http://127.0.0.1:{free_port}", retry=RetryConfig(max_retries=1, backoff_factor=0))
    api = DatasetApi(client, "CO2Emis")

    # act / assert
    with pytest.raises(requests.exceptions.ConnectionError):
        api.get()
