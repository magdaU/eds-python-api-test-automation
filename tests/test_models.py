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
            {"Minutes5UTC": "2024-01-01T00:00:00", "Minutes5DK": "2024-01-01T01:05:00", "PriceArea": "DK1", "CO2Emission": 123.4},
            {"Minutes5UTC": "2024-01-02T03:10:00", "Minutes5DK": "2024-01-02T04:15:00", "PriceArea": "DK2", "CO2Emission": 234.5},
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
        {"Minutes5UTC": "yesterday", "PriceArea": "DK1", "CO2Emission": 123.4},
        {"Minutes5UTC": "2024-01-01T00:00:00", "PriceArea": "DK3", "CO2Emission": 123.4},
    ],
    ids=["bad-utc-time", "unknown-area"],
)
def test_givenInvalidFieldValue_whenParsingRecords_thenValidationErrorIsRaised(record):
    # arrange
    response_json = {"records": [record], "total": 1}

    # act / assert
    with pytest.raises(ValidationError):
        parse_records(response_json, CO2EmisRecord)


def test_givenEmptyRecords_whenParsingRecords_thenEmptyListIsReturned():
    # arrange
    response_json = {"records": [], "total": 0}

    # act
    records = parse_records(response_json, CO2EmisRecord)

    # assert
    assert records == []


def test_givenUnknownExtraField_whenParsingRecords_thenItIsIgnored():
    # arrange
    response_json = {
        "records": [{"Minutes5UTC": "2024-01-01T00:00:00", "PriceArea": "DK1", "CO2Emission": 123.4, "NewField": "x"}],
        "total": 1,
    }

    # act
    records = parse_records(response_json, CO2EmisRecord)

    # assert
    assert records[0].CO2Emission == 123.4
    assert not hasattr(records[0], "NewField")


@pytest.mark.parametrize(
    "response_json",
    [{"total": 0}, {"records": {"not": "a list"}}, ["not", "an", "object"]],
    ids=["missing-records", "records-not-a-list", "body-not-an-object"],
)
def test_givenUnexpectedBody_whenParsingRecords_thenInvalidResponseErrorIsRaised(response_json):
    # act / assert
    with pytest.raises(InvalidResponseError, match="list under 'records'"):
        parse_records(response_json, CO2EmisRecord)


def test_givenValidDayAheadPricesJson_whenParsingRecords_thenEveryFieldIsMapped():
    # arrange
    response_json = {
        "records": [{"TimeUTC": "2024-02-03T04:15:00", "PriceArea": "SE3", "DayAheadPriceDKK": 567.8}],
        "total": 1,
    }

    # act
    records = parse_records(response_json, DayAheadPricesRecord)

    # assert
    assert len(records) == 1
    assert records[0].TimeUTC == datetime(2024, 2, 3, 4, 15)
    assert records[0].PriceArea == "SE3"
    assert records[0].DayAheadPriceDKK == 567.8


@pytest.mark.parametrize("area", ["DK1", "SE4"])
def test_givenKnownPriceArea_whenParsingDayAheadPrices_thenItIsAccepted(area):
    # arrange
    response_json = {"records": [{"PriceArea": area, "DayAheadPriceDKK": 1.5}], "total": 1}

    # act
    records = parse_records(response_json, DayAheadPricesRecord)

    # assert
    assert records[0].PriceArea == area


@pytest.mark.parametrize(
    "record",
    [
        {"TimeUTC": "2024-02-03T04:15:00", "PriceArea": "DK2"},
        {"TimeUTC": "2024-02-03T04:15:00", "PriceArea": "DK3", "DayAheadPriceDKK": 567.8},
    ],
    ids=["missing-price", "unknown-area"],
)
def test_givenInvalidDayAheadPricesRecord_whenParsingRecords_thenValidationErrorIsRaised(record):
    # arrange
    response_json = {"records": [record], "total": 1}

    # act / assert
    with pytest.raises(ValidationError):
        parse_records(response_json, DayAheadPricesRecord)


def test_givenDayAheadPricesWithoutTime_whenParsingRecords_thenTimeIsNone():
    # arrange
    response_json = {"records": [{"PriceArea": "DK1", "DayAheadPriceDKK": 12.3}], "total": 1}

    # act
    records = parse_records(response_json, DayAheadPricesRecord)

    # assert
    assert records[0].TimeUTC is None
