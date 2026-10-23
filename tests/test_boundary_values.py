import pytest

from tests.support.mocks import load_mock, records_response, sent_query


@pytest.mark.parametrize("limit", [0, 1, 2, 100000])
def test_givenLimitAtBoundary_whenGettingDataset_thenLimitIsSentUnchanged(co2_api, requests_mock, limit):
    # arrange
    requests_mock.get(co2_api.url, json=records_response([]))

    # act
    co2_api.get(limit=limit)

    # assert
    assert sent_query(requests_mock)["limit"] == [str(limit)]


@pytest.mark.parametrize("offset", [0, 1, 100000])
def test_givenOffsetAtBoundary_whenGettingDataset_thenOffsetIsSentUnchanged(co2_api, requests_mock, offset):
    # arrange
    requests_mock.get(co2_api.url, json=records_response([]))

    # act
    co2_api.get(offset=offset)

    # assert
    assert sent_query(requests_mock)["offset"] == [str(offset)]


def test_givenNoParameters_whenGettingDataset_thenNoQueryStringIsSent(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, json=records_response([]))

    # act
    co2_api.get()

    # assert
    assert sent_query(requests_mock) == {}


@pytest.mark.parametrize("parameter", ["limit", "offset"])
def test_givenNegativeValue_whenGettingDataset_thenValueIsSentAndServerRejectionIsReturned(
        co2_api, requests_mock, parameter):
    # arrange
    requests_mock.get(co2_api.url, status_code=400, json={"error": f"invalid {parameter}"})

    # act
    response = co2_api.get(**{parameter: -1})

    # assert
    assert sent_query(requests_mock)[parameter] == ["-1"]
    assert response.status_code == 400


def test_givenOffsetBeyondTotal_whenGettingDataset_thenRecordsAreEmptyButTotalIsKept(co2_api, requests_mock):
    # arrange
    total = len(load_mock("co2emis_sample.json")["records"])
    requests_mock.get(co2_api.url, json={"records": [], "total": total})

    # act
    body = co2_api.get(limit=5, offset=total + 1000).json()

    # assert
    assert body["records"] == []
    assert body["total"] == total
