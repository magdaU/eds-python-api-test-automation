import jsonschema
import pytest

from tests.support.datasets import CO2EMIS_DATASET, ELSPOTPRICES_DATASET
from tests.support.mocks import load_mock
from tests.support.schema import assert_matches_schema


def test_whenGettingCo2Emis_thenResponseMatchesSchema(co2_response):
    # act
    body = co2_response.json()

    # assert
    assert_matches_schema(body, CO2EMIS_DATASET.schema_file)


def test_whenGettingElspotprices_thenResponseMatchesSchema(elspotprices_response):
    # act
    body = elspotprices_response.json()

    # assert
    assert_matches_schema(body, ELSPOTPRICES_DATASET.schema_file)


def test_givenEmptyRecordsList_whenValidating_thenSchemaIsSatisfied():
    # arrange
    body = {"records": [], "total": 0}

    # act / assert
    assert_matches_schema(body, CO2EMIS_DATASET.schema_file)


def test_givenRecordWithoutOptionalField_whenValidating_thenSchemaIsSatisfied():
    # arrange
    body = {
        "records": [{"Minutes5UTC": "2024-01-01T00:00:00", "PriceArea": "DK1", "CO2Emission": 100.0}],
        "total": 1,
    }

    # act / assert
    assert_matches_schema(body, CO2EMIS_DATASET.schema_file)


def test_givenRecordWithoutRequiredField_whenValidating_thenValidationFails():
    # arrange
    body = {
        "records": [{"PriceArea": "DK1", "CO2Emission": 100.0}],
        "total": 1,
    }

    # act / assert
    with pytest.raises(jsonschema.exceptions.ValidationError):
        assert_matches_schema(body, CO2EMIS_DATASET.schema_file)


@pytest.mark.parametrize("break_body", [
    lambda body: body.pop("total"),
    lambda body: body.pop("records"),
    lambda body: body.update(records={"not": "a list"}),
    lambda body: body.update(total="three"),
    lambda body: body["records"].__setitem__(0, "not an object"),
], ids=["missing-total", "missing-records", "records-not-array", "total-not-integer", "record-not-object"])
def test_givenMalformedBody_whenValidating_thenValidationFails(dataset, break_body):
    # arrange
    body = load_mock(dataset.sample_response_file)
    break_body(body)

    # act / assert
    with pytest.raises(jsonschema.exceptions.ValidationError):
        assert_matches_schema(body, dataset.schema_file)
