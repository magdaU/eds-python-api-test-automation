import pytest
import requests

from client.news_api import NewsApi
from tests.support.allure_labels import labels
from tests.support.scripted_server import api_for, client_for

pytestmark = labels("Client library", "Retry behavior")

# Unlike requests_mock, a real local HTTP server sends the requests through the
# client's own HTTPAdapter/Retry, so the retry behavior itself is exercised.


@pytest.mark.parametrize("failing_statuses", [(503, 503), (429,)])
def test_givenTransientFailuresWithinRetryBudget_whenGettingDataset_thenFinalSuccessIsReturned(scripted_server, failing_statuses):
    # arrange
    server = scripted_server(*failing_statuses, 200)

    # act
    response = api_for(server).get()

    # assert
    assert response.status_code == 200
    assert server.request_count == len(failing_statuses) + 1


def test_givenPersistentServerError_whenGettingDataset_thenRetriesStopAfterMaxRetries(scripted_server):
    # arrange
    server = scripted_server(503)

    # act / assert
    with pytest.raises(requests.exceptions.RetryError):
        api_for(server, max_retries=2).get()
    assert server.request_count == 3


@pytest.mark.parametrize("status", [400, 404])
def test_givenClientError_whenGettingDataset_thenItIsNotRetried(scripted_server, status):
    # arrange
    server = scripted_server(status)

    # act
    response = api_for(server).get()

    # assert
    assert response.status_code == status
    assert server.request_count == 1


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
