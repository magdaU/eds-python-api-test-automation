from datetime import datetime

import pytest
import requests
from pydantic import ValidationError

from client.dataset_api import DatasetApi
from client.parsers import InvalidResponseError
from models.co2emis import CO2EmisRecord
from tests.support.allure_labels import labels

pytestmark = labels("Dataset API", "Typed records", "critical")


def test_givenModel_whenGettingRecords_thenTypedRecordsAreReturned(eds, co2_api):
    # arrange
    eds.dataset("CO2Emis").answers(
        records=[
            {
                "Minutes5UTC": "2024-05-06T07:08:00",
                "Minutes5DK": "2024-05-06T09:10:00",
                "PriceArea": "DK2",
                "CO2Emission": 98.7,
            }
        ]
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


def test_givenQueryParameters_whenGettingRecords_thenTheyReachTheApi(eds, dataset, dataset_api):
    # arrange
    eds.dataset(dataset.name).answers()

    # act
    dataset_api.records(
        limit=3, offset=6, sort=f"{dataset.required_field} desc", filters={"PriceArea": "DK1"}
    )

    # assert
    assert eds.last_request.query == {
        "limit": ["3"],
        "offset": ["6"],
        "sort": [f"{dataset.required_field} desc"],
        "filter": ['{"PriceArea":"DK1"}'],
    }


def test_givenNoModel_whenGettingRecords_thenTypeErrorSaysSo(eds, eds_client, dataset):
    # arrange
    api = DatasetApi(eds_client, dataset.name)
    eds.dataset(dataset.name).answers()

    # act / assert
    with pytest.raises(TypeError, match="no model"):
        api.records()
    assert eds.request_count == 0


def test_givenErrorStatus_whenGettingRecords_thenHttpErrorIsRaised(eds, dataset, dataset_api):
    # arrange
    eds.dataset(dataset.name).answers(status=400, json={"error": "invalid offset"})

    # act / assert
    with pytest.raises(requests.exceptions.HTTPError):
        dataset_api.records(offset=-1)


def test_givenBodyThatIsNotJson_whenGettingRecords_thenInvalidResponseErrorIsRaised(
    eds, dataset, dataset_api
):
    # arrange
    eds.dataset(dataset.name).answers(text="<html>maintenance</html>")

    # act / assert
    with pytest.raises(InvalidResponseError, match="did not return JSON"):
        dataset_api.records()


def test_givenUnknownPriceArea_whenGettingRecords_thenValidationErrorIsRaised(eds, co2_api):
    # arrange
    eds.dataset("CO2Emis").answers(
        records=[{"Minutes5UTC": "2024-05-06T07:08:00", "PriceArea": "DK3", "CO2Emission": 98.7}]
    )

    # act / assert
    with pytest.raises(ValidationError):
        co2_api.records()
