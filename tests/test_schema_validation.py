import jsonschema
import pytest

from tests.support.allure_labels import labels
from tests.support.datasets import CO2EMIS_DATASET, DAYAHEADPRICES_DATASET
from tests.support.live import TRANSIENT_NETWORK_ERRORS
from tests.support.mocks import load_mock
from tests.support.schema import assert_matches_schema

pytestmark = labels("Dataset API", "Schema validation", "critical")


@pytest.mark.live
@pytest.mark.flaky(reruns=1, reruns_delay=5, only_rerun=TRANSIENT_NETWORK_ERRORS)
def test_whenGettingCo2Emis_thenResponseMatchesSchema(co2_response):
    # assert
    assert co2_response.status_code == 200
    body = co2_response.json()
    assert body["records"], "no records returned, so the schema was not exercised on any record"
    assert_matches_schema(body, CO2EMIS_DATASET.schema_file)


@pytest.mark.live
@pytest.mark.flaky(reruns=1, reruns_delay=5, only_rerun=TRANSIENT_NETWORK_ERRORS)
def test_whenGettingDayAheadPrices_thenResponseMatchesSchema(dayaheadprices_latest):
    # assert
    assert dayaheadprices_latest.status_code == 200
    body = dayaheadprices_latest.json()
    assert body["records"], "no records returned, so the schema was not exercised on any record"
    assert_matches_schema(body, DAYAHEADPRICES_DATASET.schema_file)


def test_givenEmptyRecordsList_whenValidating_thenSchemaIsSatisfied():
    # arrange
    body = {"records": [], "total": 0, "limit": 5, "dataset": CO2EMIS_DATASET.name}

    # act / assert
    assert_matches_schema(body, CO2EMIS_DATASET.schema_file)


def test_givenRecordWithoutOptionalField_whenValidating_thenSchemaIsSatisfied(dataset):
    # arrange
    body = load_mock(dataset.sample_response_file)
    del body["records"][0][dataset.optional_field]

    # act / assert
    assert_matches_schema(body, dataset.schema_file)


def test_givenRecordWithTextAsValue_whenValidating_thenValidationFails(dataset):
    # arrange
    body = load_mock(dataset.sample_response_file)
    body["records"][0][dataset.value_field] = "not-a-number"

    # act / assert
    with pytest.raises(jsonschema.exceptions.ValidationError):
        assert_matches_schema(body, dataset.schema_file)


def test_givenRecordWithoutRequiredField_whenValidating_thenValidationFails(dataset):
    # arrange
    body = load_mock(dataset.sample_response_file)
    del body["records"][0][dataset.required_field]

    # act / assert
    with pytest.raises(jsonschema.exceptions.ValidationError):
        assert_matches_schema(body, dataset.schema_file)


@pytest.mark.parametrize(
    "break_body",
    [
        lambda body: body.update(records={"not": "a list"}),
        lambda body: body.update(total="three"),
        lambda body: body.pop("limit"),
        lambda body: body.pop("dataset"),
    ],
    ids=["records-not-array", "total-not-integer", "missing-limit", "missing-dataset"],
)
def test_givenMalformedBody_whenValidating_thenValidationFails(break_body):
    # arrange
    # both dataset schemas share the same envelope, so one dataset is enough
    body = load_mock(CO2EMIS_DATASET.sample_response_file)
    break_body(body)

    # act / assert
    with pytest.raises(jsonschema.exceptions.ValidationError):
        assert_matches_schema(body, CO2EMIS_DATASET.schema_file)
