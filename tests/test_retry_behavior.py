import pytest
import requests

from client.news_api import NewsApi
from tests.support.allure_labels import labels
from tests.support.scripted_server import api_for, client_for

pytestmark = labels("Client library", "Retry behavior", "critical")

# Unlike requests_mock, a real local HTTP server sends the requests through the
# client's own HTTPAdapter/Retry, so the retry behavior itself is exercised.


def test_givenThrottledOnce_whenGettingDataset_thenFinalSuccessIsReturned(scripted_server):
    # arrange
    server = scripted_server(429, 200)

    # act
    response = api_for(server).get()

    # assert
    assert response.status_code == 200
    assert server.request_count == 2


def test_givenPersistentServerError_whenGettingNews_thenRetriesStopAfterMaxRetries(scripted_server):
    # arrange
    server = scripted_server(500)
    news_api = NewsApi(client_for(server, max_retries=2))

    # act / assert
    with pytest.raises(requests.exceptions.RetryError):
        news_api.get()
    assert server.request_count == 3


def test_givenZeroMaxRetries_whenServerFails_thenNoRetryIsMade(scripted_server):
    # arrange
    server = scripted_server(503)

    # act / assert
    with pytest.raises(requests.exceptions.RetryError):
        api_for(server, max_retries=0).get()
    assert server.request_count == 1
