import pytest
from pydantic import ValidationError

from client.parsers import parse_records
from models.co2emis import CO2EmisRecord


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
