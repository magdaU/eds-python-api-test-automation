import pytest
from pydantic import ValidationError

from client.parsers import parse_records
from models.co2emis import CO2EmisRecord


def test_parse_records_returns_typed_models_for_valid_json():
    response_json = {
        "records": [
            {"Minutes5UTC": "2024-01-01T00:00:00", "Minutes5DK": "2024-01-01T01:00:00", "PriceArea": "DK1", "CO2Emission": 123.4},
            {"Minutes5UTC": "2024-01-01T00:05:00", "Minutes5DK": "2024-01-01T01:05:00", "PriceArea": "DK2", "CO2Emission": 234.5},
        ],
        "total": 2,
    }

    records = parse_records(response_json, CO2EmisRecord)

    assert len(records) == 2
    assert records[0].PriceArea == "DK1"
    assert records[0].CO2Emission == 123.4
    assert records[1].PriceArea == "DK2"
    assert records[1].CO2Emission == 234.5


def test_parse_records_raises_on_missing_required_field():
    response_json = {
        "records": [
            {"PriceArea": "DK1", "CO2Emission": 123.4},
        ],
        "total": 1,
    }

    with pytest.raises(ValidationError):
        parse_records(response_json, CO2EmisRecord)
