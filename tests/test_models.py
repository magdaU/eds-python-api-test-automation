from datetime import datetime

import pytest
from pydantic import ValidationError

from client.parsers import InvalidResponseError, parse_records
from models.co2emis import CO2EmisRecord
from models.dayaheadprices import DayAheadPricesRecord
from tests.support.allure_labels import labels

pytestmark = labels("Dataset API", "Pydantic models", "critical")


def test_givenValidJson_whenParsingRecords_thenTypedModelsAreReturned():
    # arrange
    response_json = {
        "records": [
            {
                "Minutes5UTC": "2024-01-01T00:00:00",
                "Minutes5DK": "2024-01-01T01:05:00",
                "PriceArea": "DK1",
                "CO2Emission": 123.4,
            },
            {
                "Minutes5UTC": "2024-01-02T03:10:00",
                "Minutes5DK": "2024-01-02T04:15:00",
                "PriceArea": "DK2",
                "CO2Emission": 234.5,
            },
        ],
        "total": 2,
    }

    # act
    records = parse_records(response_json, CO2EmisRecord)

    # assert
    assert len(records) == 2
    assert records[0].Minutes5UTC == datetime(2024, 1, 1, 0, 0)
    assert records[0].Minutes5DK == datetime(2024, 1, 1, 1, 5)
    assert records[0].PriceArea == "DK1"
    assert records[0].CO2Emission == 123.4
    assert records[1].Minutes5UTC == datetime(2024, 1, 2, 3, 10)
    assert records[1].Minutes5DK == datetime(2024, 1, 2, 4, 15)
    assert records[1].PriceArea == "DK2"
    assert records[1].CO2Emission == 234.5


def test_givenRecordWithoutRequiredField_whenParsingRecords_thenValidationErrorIsRaised():
    # arrange
    response_json = {"records": [{"PriceArea": "DK1", "CO2Emission": 123.4}], "total": 1}

    # act / assert
    with pytest.raises(ValidationError):
        parse_records(response_json, CO2EmisRecord)


@pytest.mark.parametrize(
    "record",
    [
        {"Minutes5UTC": "2024-01-01T00:00:00", "PriceArea": "DK3", "CO2Emission": 123.4},
    ],
    ids=["unknown-area"],
)
def test_givenInvalidFieldValue_whenParsingRecords_thenValidationErrorIsRaised(record):
    # arrange
    response_json = {"records": [record], "total": 1}

    # act / assert
    with pytest.raises(ValidationError):
        parse_records(response_json, CO2EmisRecord)


@pytest.mark.parametrize(
    "response_json",
    [{"total": 0}, ["not", "an", "object"]],
    ids=["missing-records", "body-not-an-object"],
)
def test_givenUnexpectedBody_whenParsingRecords_thenInvalidResponseErrorIsRaised(response_json):
    # act / assert
    with pytest.raises(InvalidResponseError, match="list under 'records'"):
        parse_records(response_json, CO2EmisRecord)


def test_givenRequiredFieldMissing_whenParsingRecords_thenValidationErrorIsRaised():
    # arrange
    co2 = {"Minutes5UTC": "2024-01-01T00:00:00", "PriceArea": "DK1", "CO2Emission": 123.4}
    price = {"TimeUTC": "2024-02-03T04:15:00", "PriceArea": "DK2", "DayAheadPriceDKK": 567.8}
    cases = [
        (CO2EmisRecord, {k: v for k, v in co2.items() if k != "PriceArea"}),
        (CO2EmisRecord, {k: v for k, v in co2.items() if k != "CO2Emission"}),
        (DayAheadPricesRecord, {k: v for k, v in price.items() if k != "PriceArea"}),
        (DayAheadPricesRecord, {k: v for k, v in price.items() if k != "DayAheadPriceDKK"}),
    ]

    # act / assert
    for model, record in cases:
        with pytest.raises(ValidationError):
            parse_records({"records": [record], "total": 1}, model)


def test_givenUnknownAreaOrTextPrice_whenParsingDayAheadPrices_thenValidationErrorIsRaised():
    # arrange
    records = [
        {"TimeUTC": "2024-02-03T04:15:00", "PriceArea": "XX9", "DayAheadPriceDKK": 567.8},
        {"TimeUTC": "2024-02-03T04:15:00", "PriceArea": "DK2", "DayAheadPriceDKK": "expensive"},
    ]

    # act / assert
    for record in records:
        with pytest.raises(ValidationError):
            parse_records({"records": [record], "total": 1}, DayAheadPricesRecord)
