import json

import jsonschema
import pytest


def _assert_matches_schema(json_body, schema_filename):
    with open(f"schemas/{schema_filename}") as f:
        schema = json.load(f)

    jsonschema.validate(instance=json_body, schema=schema)


def test_co2_response_matches_schema(co2_response):
    _assert_matches_schema(co2_response.json(), "co2emis_schema.json")


def test_elspotprices_response_matches_schema(elspotprices_response):
    _assert_matches_schema(elspotprices_response.json(), "elspotprices_schema.json")


def test_empty_records_list_is_valid():
    body = {"records": [], "total": 0}

    _assert_matches_schema(body, "co2emis_schema.json")


def test_record_missing_optional_field_is_valid():
    body = {
        "records": [{"Minutes5UTC": "2024-01-01T00:00:00", "PriceArea": "DK1", "CO2Emission": 100.0}],
        "total": 1,
    }

    _assert_matches_schema(body, "co2emis_schema.json")


def test_record_missing_required_field_is_invalid():
    body = {
        "records": [{"PriceArea": "DK1", "CO2Emission": 100.0}],
        "total": 1,
    }

    with pytest.raises(jsonschema.exceptions.ValidationError):
        _assert_matches_schema(body, "co2emis_schema.json")
