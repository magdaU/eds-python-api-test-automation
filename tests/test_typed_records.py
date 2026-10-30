from datetime import datetime

import pytest
import requests
from pydantic import ValidationError

from client.dataset_api import DatasetApi
from models.co2emis import CO2EmisRecord
from tests.support.allure_labels import labels
from tests.support.mocks import records_response, sent_query

pytestmark = labels("Dataset API", "Typed records", "critical")


def test_givenModel_whenGettingRecords_thenTypedRecordsAreReturned(co2_api, requests_mock):
    # arrange
    requests_mock.get(
        co2_api.url,
        json=records_response(
            [{"Minutes5UTC": "2024-05-06T07:08:00", "Minutes5DK": "2024-05-06T09:10:00", "PriceArea": "DK2", "CO2Emission": 98.7}]
        ),
    )

    # act
    records = co2_api.records()

    # assert
    assert len(records) == 1
    assert isinstance(records[0], CO2EmisRecord)
    assert records[0].Minutes5UTC == datetime(2024, 5, 6, 7, 8)
    assert records[0].Minutes5DK == datetime(2024, 5, 6, 9, 10)
    assert records[0].PriceArea == "DK2"
    assert records[0].CO2Emission == 98.7


def test_givenQueryParameters_whenGettingRecords_thenTheyReachTheApi(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, json=records_response([]))

    # act
    co2_api.records(limit=3, offset=6, sort="Minutes5UTC desc", filters={"PriceArea": "DK1"})

    # assert
    assert sent_query(requests_mock) == {
        "limit": ["3"],
        "offset": ["6"],
        "sort": ["Minutes5UTC desc"],
        "filter": ['{"PriceArea":"DK1"}'],
    }


def test_givenNoModel_whenGettingRecords_thenTypeErrorSaysSo(eds_client, requests_mock):
    # arrange
    api = DatasetApi(eds_client, "CO2Emis")
    requests_mock.get(api.url, json=records_response([]))

    # act / assert
    with pytest.raises(TypeError, match="no model"):
        api.records()
    assert requests_mock.call_count == 0


def test_givenErrorStatus_whenGettingRecords_thenHttpErrorIsRaised(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, status_code=400, json={"error": "invalid offset"})

    # act / assert
    with pytest.raises(requests.exceptions.HTTPError):
        co2_api.records(offset=-1)


def test_givenUnknownPriceArea_whenGettingRecords_thenValidationErrorIsRaised(co2_api, requests_mock):
    # arrange
    requests_mock.get(
        co2_api.url, json=records_response([{"Minutes5UTC": "2024-05-06T07:08:00", "PriceArea": "DK3", "CO2Emission": 98.7}])
    )

    # act / assert
    with pytest.raises(ValidationError):
        co2_api.records()
