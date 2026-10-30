import pytest

from tests.support.allure_labels import labels
from tests.support.mocks import records_response, sent_query

pytestmark = labels("Dataset API", "Boundary values")


@pytest.mark.parametrize("limit", [0, 1])
def test_givenLimitAtBoundary_whenGettingDataset_thenLimitIsSentUnchanged(co2_api, requests_mock, limit):
    # arrange
    requests_mock.get(co2_api.url, json=records_response([]))

    # act
    co2_api.get(limit=limit)

    # assert
    assert sent_query(requests_mock)["limit"] == [str(limit)]


def test_givenZeroOffset_whenGettingDataset_thenOffsetIsSentUnchanged(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, json=records_response([]))

    # act
    co2_api.get(offset=0)

    # assert
    assert sent_query(requests_mock)["offset"] == ["0"]


def test_givenNoParameters_whenGettingDataset_thenNoQueryStringIsSent(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, json=records_response([]))

    # act
    co2_api.get()

    # assert
    assert sent_query(requests_mock) == {}


def test_givenNegativeOffset_whenGettingDataset_thenValueIsSentAndServerRejectionIsReturned(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, status_code=400, json={"error": "invalid offset"})

    # act
    response = co2_api.get(offset=-1)

    # assert
    assert sent_query(requests_mock)["offset"] == ["-1"]
    assert response.status_code == 400
