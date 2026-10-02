import pytest
import requests

from client.dataset_api import DatasetApi

# requests_mock replaces how the session dispatches requests entirely, so the
# custom HTTPAdapter/Retry mounted on EDSApiClient's session never runs against
# a mocked response (verified: any mocked status code yields call_count == 1,
# retryable or not). Retry *configuration* is covered at the unit level in
# test_eds_client.py instead of end-to-end here.


def test_givenInvalidDataset_whenGettingIt_thenBadRequestIsReturned(eds_client, requests_mock):
    # arrange
    invalid_dataset_api = DatasetApi(eds_client, "InvalidDataset")
    requests_mock.get(invalid_dataset_api.url, status_code=400, json={"error": "invalid dataset"})

    # act
    response = invalid_dataset_api.get()

    # assert
    assert response.status_code == 400


def test_givenUnknownPath_whenGettingDataset_thenNotFoundIsReturned(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, status_code=404)

    # act
    response = co2_api.get()

    # assert
    assert response.status_code == 404


def test_givenConnectionTimeout_whenGettingDataset_thenTimeoutIsRaised(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, exc=requests.exceptions.ConnectTimeout)

    # act / assert
    with pytest.raises(requests.exceptions.ConnectTimeout):
        co2_api.get()
