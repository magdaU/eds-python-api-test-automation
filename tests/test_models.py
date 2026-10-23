import pytest
from pydantic import ValidationError

from client.parsers import parse_records
from models.co2emis import CO2EmisRecord
from models.elspotprices import ElspotpricesRecord


def test_givenValidJson_whenParsingRecords_thenTypedModelsAreReturned():
    # arrange
    response_json = {
        "records": [
            {"Minutes5UTC": "2024-01-01T00:00:00", "Minutes5DK": "2024-01-01T01:00:00", "PriceArea": "DK1", "CO2Emission": 123.4},
            {"Minutes5UTC": "2024-01-01T00:05:00", "Minutes5DK": "2024-01-01T01:05:00", "PriceArea": "DK2", "CO2Emission": 234.5},
        ],
        "total": 2,
    }

    # act
    records = parse_records(response_json, CO2EmisRecord)

    # assert
    assert len(records) == 2
    assert records[0].Minutes5UTC == "2024-01-01T00:00:00"
    assert records[0].Minutes5DK == "2024-01-01T01:00:00"
    assert records[0].PriceArea == "DK1"
    assert records[0].CO2Emission == 123.4
    assert records[1].Minutes5UTC == "2024-01-01T00:05:00"
    assert records[1].Minutes5DK == "2024-01-01T01:05:00"
    assert records[1].PriceArea == "DK2"
    assert records[1].CO2Emission == 234.5


def test_givenRecordWithoutRequiredField_whenParsingRecords_thenValidationErrorIsRaised():
    # arrange
    response_json = {"records": [{"PriceArea": "DK1", "CO2Emission": 123.4}], "total": 1}

    # act / assert
    with pytest.raises(ValidationError):
        parse_records(response_json, CO2EmisRecord)


@pytest.mark.parametrize("record", [
    {"Minutes5UTC": "2024-01-01T00:00:00", "PriceArea": "DK1", "CO2Emission": "not-a-number"},
    {"Minutes5UTC": "2024-01-01T00:00:00", "PriceArea": None, "CO2Emission": 123.4},
    {"Minutes5UTC": "2024-01-01T00:00:00", "PriceArea": "DK1", "CO2Emission": None},
], ids=["wrong-type", "null-string", "null-number"])
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


def test_givenResponseWithoutRecordsKey_whenParsingRecords_thenKeyErrorIsRaised():
    # arrange
    response_json = {"total": 0}

    # act / assert
    with pytest.raises(KeyError):
        parse_records(response_json, CO2EmisRecord)


def test_givenValidElspotpricesJson_whenParsingRecords_thenEveryFieldIsMapped():
    # arrange
    response_json = {
        "records": [{"HourUTC": "2024-02-03T04:00:00", "PriceArea": "DK2", "SpotPriceDKK": 567.8}],
        "total": 1,
    }

    # act
    records = parse_records(response_json, ElspotpricesRecord)

    # assert
    assert len(records) == 1
    assert records[0].HourUTC == "2024-02-03T04:00:00"
    assert records[0].PriceArea == "DK2"
    assert records[0].SpotPriceDKK == 567.8


def test_givenElspotpricesWithoutHour_whenParsingRecords_thenHourIsNone():
    # arrange
    response_json = {"records": [{"PriceArea": "DK1", "SpotPriceDKK": 12.3}], "total": 1}

    # act
    records = parse_records(response_json, ElspotpricesRecord)

    # assert
    assert records[0].HourUTC is None
